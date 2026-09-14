#!/usr/bin/env python3
"""
warren_flood_prep.py — step 1 of W94 (D-159): the warren mask, by frame date.

WHAT THIS IS, AND WHAT IT IS NOT

  A TOOL, not a pipeline step. It writes to `working/updates/`, not `outputs/`,
  and it is not in the manifest. That is deliberate: D-159's method has a
  falsification test it has not yet faced — the May frame must come back empty
  of flood patches — and registering a step whose method may not survive would
  move the documented pipeline counts for something provisional. When the method
  is proven it becomes a numbered script with its outputs in `outputs/`.

WHAT IT DOES

  1. Derives canopy closure per variable block from the committed Script 41
     index (`utils.warren_mask.closure_dates`), and writes the table.
  2. Writes the warren and canopy areas for every frame date in the manifest.
  3. Writes the warren polygon once per CANOPY EPOCH — the distinct states the
     mask takes across the series — as GeoJSON and KML, so it can be opened in
     Google Earth against the frames themselves.
  4. Reports which DEM basins fall inside the warren, since those are the basins
     a flood reading can be attributed to.

  Everything here is polygon and DEM work. No imagery is read.

NOT DONE HERE, AND WHY

  **The repeat-floor drift test cannot run yet.** The specification lists it as
  step 1, which was wrong: comparing a slack's floor elevation between two dates
  needs DIGITISED OUTLINES on both, and there are none. The 2023 LiDAR against
  2006-2026 frames remains an open assumption; the substitute check available
  today is the DEM-minus-DGPS residual (median +0.050 m, MAD 0.030 m at 81
  wells), and what would make it decisive is the DGPS survey DATE, which no
  record in this tree states.

  See D-159 and `working/updates/NRG_spec_W94_warren_flood_surface_2026-09-11.md`.
"""
from __future__ import annotations

__version__ = "1.26.0"  # Hollingham (2026) - 2026-09-14. THE BUSH MASK IS
#   TWO-SIDED (Martin): a tree reads as no water on a dry frame, but where it
#   sits in a hollow that reads wet it COUNTS AS WET - the canopy hides the
#   ground, it does not drain it. A bush cell carries no evidence of its own and
#   takes it from its hollow, restored only where the hollow holds classified
#   water elsewhere AND the cell sits at or below that water's level (D-159:
#   water is level). The dry case needs no special rule: no water classified,
#   nothing restored. 2021-03-24 reads 62.57 ha with 21.63 ha restored,
#   precision 0.84 against 0.75 before.
# v1.25.0  # Hollingham (2026) - 2026-09-14. Bushes are EXCLUDED
#   at source: phase 8 drops the mask's cells from `usable` before the open-dune
#   reference and before any threshold, so scrub cannot be read as water on any
#   frame. The mask is phase 19's dry-frame dark ground plus Martin's
#   warren_tree_mask.kml (8.34 ha, on disk since 09-12 and previously read by no
#   code) LESS drinking_pools.kml, the standing water that survives a drought and
#   must never be masked. 20.39 ha, 3.55 ha of it inside a hollow - which is the
#   stated cost, every area being a lower bound by that much. D-167.
# v1.24.0  # Hollingham (2026) - 2026-09-14. --cut-z: phase 8
#   cuts at a threshold the frame did not choose, written to a _fixedz set of
#   its own. z is standardised against each frame's own open dune, so a cut in z
#   transfers between frames. The gate's own z = -0.75 applied to 2019-09-11
#   returns 76 bodies and 16.48 ha with all 50 wells agreed, against 668 bodies
#   and 288.44 ha when that frame chose its own split. Phase 19 rebuilt on the
#   fixed-cut reads; the figure caption no longer calls a fixed cut the frame's
#   own. D-167.
# v1.23.0  # Hollingham (2026) - 2026-09-14. PHASE 19, the
#   false-wet mask (D-167). Martin: the dry frames were given so that dark
#   features which look like water could be digitised and removed, NOT as a
#   zero-water gate on a model. A forced read of 2009-04-20 - no water in it -
#   returns 87.86 ha against 88.31 ha for the wettest frame in the corpus.
#   Every imagery area published before today is an upper bound.
# v1.22.0  # Hollingham (2026) - 2026-09-13. PHASE 18 (T-27):
#   the hollow as a dipwell. Script 11b's collapsed threshold P_flood = A*d + B
#   is applied at a slack floor instead of a well's ground, and the flooded area
#   inside a hollow comes from that hollow's own DEM hypsometry. Mode C is
#   climatological; Mode V re-runs it with the year's observed summer minimum and
#   the winter's actual P and PET, truncated at the read month (Martin, 2026-09-13),
#   scored against every read and the four dry controls. NOTHING IS FITTED TO THE
#   IMAGERY, which is what phase 17 could not say. A self-test drives the forward
#   recurrence with the closed form's own solution and refuses to run if they
#   disagree. Outputs to working/updates only: NOT a pipeline step, pending Mode V.
# v1.21.0  # Hollingham (2026) - 2026-09-13. Readings collected after
#   the pipeline's raw inputs were frozen reach the flood work through
#   data/flood_calibration_levels.csv and _merge_calibration(), NOT through
#   Newborough_Cleaned_For_Model.csv. Appending March 2026 to the pipeline input
#   instead re-fitted everything downstream and moved the synthetic clearfell step
#   from p = 0.000879 to p = 0.0010117, breaking a published p < 0.001 claim.
#   Calibrating a map must not move a significance test. The merge never
#   overwrites a month the pipeline already has.
# v1.20.0  # Hollingham (2026) - 2026-09-13. Phase 17 regresses the
#   hollow wet fraction on site wetness and place properties, trained on both reads.
#   It learns WHERE well - depth, area, floor and EWI all strongly signed - and WHEN
#   badly: leave-one-DATE-out returns 156.94 ha against 46.09 observed on
#   2021-03-24 and 0.00 against 20.10 on 2020-03-31, because three informative
#   dates cannot support a temporal coefficient. NOT usable for a series yet; the
#   constraint is dated reads, not the fit.
# v1.19.0  # Hollingham (2026) - 2026-09-13. --form depth builds the
#   water table as h interpolated onto the SMOOTHED ground rather than as an
#   absolute elevation, which is the variable the SSM is written in. Specced with
#   its gate stated first, and IT FAILS THAT GATE: the wettest date goes 17.43 ->
#   34.77 ha and much closer to the imagery, but 2010-05-27 - a dry control with
#   ZERO wet dipwells - goes 2.31 -> 16.14 ha and the margin falls 4.50 -> 2.2 : 1,
#   below DRY_CONTROL_MIN_RATIO. NOT adopted; elevation remains the default.
# v1.18.0  # Hollingham (2026) - 2026-09-13. Phase 16 diagnoses the
#   per-slack shortfall: of 1,236 slack units the imagery says are wet, the model
#   misses 714 by a MEDIAN OF 1.278 m, with an IQR of 1.453 m - too wide and far
#   too large to be a constant. The missed slacks sit at a median floor of 9.10 m
#   AOD against 4.17 m for those the model gets, which is the signature of IDW on
#   absolute elevation flattening the water-table MOUND. Not a tuning problem.
# v1.17.0  # Hollingham (2026) - 2026-09-13. DEFECT FIX in
#   _well_levels: the day <= 15 branch used `d - MonthBegin(1)`, which from a
#   mid-month date rolls back to the first of the SAME month, so the bucketing the
#   docstring describes was never applied. One read date has day <= 15 and it is
#   the one Martin queried: the 2021-04-04 frame was scored against the
#   END-OF-APRIL water table (median -0.260 m, 14 wells at or above ground) when
#   it was taken on the 4th, eleven days after 2021-03-24 whose end-of-March level
#   is +0.020 m with 41 wells at or above ground. 13.21 -> 17.43 ha, now equal to
#   2021-03-24 because both frames sit within days of the same month end.
# v1.16.0  # Hollingham (2026) - 2026-09-13. Phase 15 sweeps
#   SLACK_MIN_DEPTH_M against the imagery, because only 28.8 % of the water the
#   2021-03-24 read sees lies inside a slack unit at all. The merge tree does not
#   depend on the threshold, so _slack_units now takes depth/area and caches the
#   tree; the sweep rebuilds nothing. Phase 13 gains --kml, writing the predicted
#   flood as polygons to be judged on the imagery in Google Earth rather than
#   against a number.
# v1.15.0  # Hollingham (2026) - 2026-09-13. Phase 14: the monthly
#   flooded-area series, phase 13 run over every month instead of eight imagery
#   dates. TWO bases, because the network trebles across the record and a series on
#   whatever wells exist each month cannot separate a rising water table from a
#   growing dipwell network: a fixed 57-well panel (SERIES_PANEL_*) as the headline
#   and all-available as the sensitivity. Measured LOO saturates at ~55 wells, so
#   fixing composition costs nothing. --frames renders one map per month for an
#   animation (tools/make_flood_animation.sh); the frames are working files and are
#   gitignored. --months N smoke-tests the phase; a partial series is not an artefact.
# v1.14.0  # Hollingham (2026) - 2026-09-13. Phase 9: the raster bias
#   is measured from DGPS-surveyed wells ONLY (PHASE9_BIAS_GROUND_SOURCES) - a well
#   whose ground came from the DEM cannot measure the DEM, and those six pairs sat
#   at -0.037 m / MAD 0.153 against the DGPS pairs' +0.302 / 0.083 - and the
#   waterline basis is PINNED to vp2 (PHASE9_WATERLINE_BASIS) rather than taken
#   from whichever polygons exist, which had the code on tiles while the committed
#   constant was vp2's. PHASE9_DEM_BIAS_M 0.282 -> 0.302, pending the read-back.
#   The unthresholded frame was tested here and rejected: two pairs, both circular.
# v1.13.0  # Hollingham (2026) - 2026-09-13. Phase 13 reads the
#   UNTHRESHOLDED level frame via _level_frame(): 01_wells_all.csv when Script 01
#   >= 1.16.0 has emitted it, else 01_wells_clean.csv with a warning. Recovers the
#   five DGPS-surveyed south-eastern wells (D31/D33/D34/D39/D45) that Script 01's
#   SSM/clustering admission thresholds drop; on 2010-05-27, the one read date
#   inside their record, the dry-control false positive falls 4.49 -> 2.15 ha and
#   the wet/dry margin rises 3.5 -> 4.5 : 1. z_b = 0 m AOD retained: the midpoint
#   to MHWS (+1.45) was tested against the same frame and is worse on every dry
#   control (worst 3.75 -> 7.47 ha, margin 4.5 -> 2.9 : 1).
# v1.12.0  # Hollingham (2026) - 2026-09-13. Phase 13, the
#   flooded extent under Martin's definition - the water table above the
#   slack floor. Three corrections make it survive its own controls:
#   merge-tree slack units instead of hollows (composites and basins that
#   drain to the sea are gone), the lake gauge out of the interpolation, and
#   the ESTUARY AS A BOUNDARY CONDITION (Martin), which fixes the
#   estuary-facing flank for a physical reason where a distance cap would
#   have discarded a fifth of the warren on every date.
# 1.11.0  Hollingham (2026) - 2026-09-13. Phase 10's three
#   contrasts are COMBINED into one signed score rather than thresholded
#   singly, and the glare branch is removed: it tested for
#   brighter-and-desaturated, where the measurement says water is MORE
#   saturated than its rim, so it voted against its own signal. Glare
#   applies to 2021-04-04 alone (Martin) and is an exception, not a branch.
#   The covered-fraction gate is retired for a reported bound.
# 1.10.0  Hollingham (2026) - 2026-09-12. Phase 11 takes
#   --series vp2, where the shared transform means the pair needs no
#   alignment at all, and it WORKS there: 2021-03-24 against 2009-04-20
#   returns 12.12 ha at precision 1.000 against a dry-pair control of
#   0.37 ha. A go/no-go gate (PAIR_MIN_R) now refuses any pair that does
#   not agree on ground that cannot have changed — the check whose absence
#   let the broken tile registrations produce a plausible answer.
# 1.9.0  Hollingham (2026) - 2026-09-12. Phase 11,
#   bi-temporal change detection (Martin's design): the wet date against a
#   dry one, so the reference is THE SAME GROUND at another date and the dune
#   texture cancels on differencing instead of having to be averaged away.
#   Co-registered on unchanged ground only, two-sided for glare, and the
#   noise floor measured from the dune rather than assumed. A dry-against-dry
#   pair is the control and it cannot be passed by construction.
# 1.8.0  Hollingham (2026) - 2026-09-12. Phase 10, the
#   slack-edge classifier: each slack judged against its OWN rim, inside one
#   tile, so exposure, sun angle, view geometry and dune texture cancel. The
#   test is TWO-SIDED because the sun and clouds reflect off the pools and
#   turn the water white (Martin), which a dark-water detector scores as
#   drier than sand. Stale imagery is found by per-cell IDENTITY with an
#   earlier date, not by hunting a colour seam. The DEM supplies geometry
#   and never promotes a slack.
# 1.7.0  Hollingham (2026) - 2026-09-12. The flood read
#   takes a --series: "tiles" mosaics the 2026-09-12 captures at a per-cell
#   median near 1.0 m/px, "vp2" is the 2.884 m/px read it replaces.
#   Identical code after the sampling step, so a difference between them is
#   resolution and registration, not method. The TILE READ IS PRIMARY and
#   the vp2 read is the sensitivity check, fixed before either was run.
#   Artefacts carry a _tiles tag, and W94_09_scores is now merged by date
#   instead of overwritten by a partial run.  # Hollingham (2026) - 2026-09-11. PHASE 8, the flood read
#   (D-159, spec NRG_spec_W94_phase8_flood_read_2026-09-11.md). The photographs
#   classify and the DEM only names the result. Each frame is normalised against
#   its OWN OPEN DUNE - the warren less the hollows, never flooded by
#   construction - so the cut is exposure-free across five rights-holders; a
#   BIMODALITY GATE lets a dry frame return DRY, which plain Otsu cannot, and
#   that is what lets a dry frame fail the method. (CORRECTED 2026-09-12: the
#   two "May negatives" are ONE frame — see D-159 — so that test is weaker than
#   this note originally claimed.) The vp2
#   transform is cached as CONTROL POINTS (registration costs two minutes), and
#   one transform serves every vp2 frame - measured, which is what lets
#   2010-05-27 be read at all. `--phase` and `--date` added; the tool is no
#   longer all-or-nothing. THE CUT IS EACH FRAME'S OWN OTSU THRESHOLD, gated on
#   where that threshold falls (config 1.40.0): measured on five frames, the
#   between-class variance separates wet from dry by 0.713 against 0.604 and the
#   threshold POSITION by 1.15 z, so the gate moved to the statistic that
#   carries the signal and no value is frozen from one frame onto fifteen.
#   --calibrate MERGES by date rather than overwriting:
#   the cut comes from a wet frame and the gate from frames the record says are
#   dry, so the file is built up across runs.
#   1.6.0: PHASE 9, Delta - the slack-bottom offset the Q4 analysis put behind
#   a field campaign. Three units emitted, scored against the July bound, which
#   carries no DEM and no imagery. The raster's local bias is measured here from
#   the waterlines rather than assumed.
#   1.5.0: a date that comes back DRY or SKIPPED now REMOVES any flood polygons,
#   map and per-well CSV left for it by an earlier, wider gate. Two such files
#   survived the gate going from -0.30 back to -0.75 and read as results.
# v1.3.0 superseded within the day; see the note above.
# v1.2.0  # Hollingham (2026) - 2026-09-11. THE HOLLOW AND THE
#   SLACK ARE SEPARATED. A depression was SELECTED on holding SLACK_MIN_DEPTH_M
#   and then DRAWN floor-to-spill, so every internal rise inside it was mapped as
#   slack - the ridge Martin can see near CEH32. Measured on that node: 5.60 ha
#   drawn, 0.01 ha wet at floor + 0.10 m, 89 % of it more than 0.5 m above its
#   own floor; area-weighted over 400 slacks the wet fraction is 0.05. Phase 6
#   now emits BOTH - `W94_06_hollows.*`, the node extent, which is the
#   attribution unit, and `W94_06_slacks.*`, the surface at floor +
#   SLACK_MIN_DEPTH_M, which is the wet area and the thing a photograph can be
#   compared with. "Hollow" rather than the spec's "basin" because phases 4 and 5
#   already use `basin` for the Ranwell catchments. D-159.
# v1.1.0  # Hollingham (2026) - 2026-09-11. SLACKS, delineated from
#   the DEM as closed depressions, replace the Ranwell prototype basins as the
#   scoring unit (Martin: "the basins are too large and don't represent the
#   slacks"). Phase 4 now reports both, so the scale difference is visible
#   rather than asserted.
# v1.0.0  # Hollingham (2026) - 2026-09-11. New, for D-159 step 1.

import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import geopandas as gpd                                      # noqa: E402
import numpy as np                                           # noqa: E402
import pandas as pd                                          # noqa: E402
import rasterio                                              # noqa: E402
from rasterio.mask import mask as rio_mask                    # noqa: E402

from utils.config import CANOPY_CLOSURE_RATIO                 # noqa: E402
from utils.console_utils import banner, info, phase, saved, step, warn  # noqa: E402
from utils.paths import DATA_DEM, DATA_GEO_DIR                # noqa: E402
from utils.warren_mask import (OSGB, _features, canopy_on, closure_dates,
                               warren_on)  # noqa: E402

OUT = REPO / "working" / "updates"
MANIFEST = DATA_GEO_DIR / "aerial_manifest.csv"
# Ground that is dark in every frame and is not water (Martin, 2026-09-14), and
# the standing water that must never be mistaken for it.
BUSH_MASK_KML = DATA_GEO_DIR / "warren_tree_mask.kml"
STANDING_WATER_KML = DATA_GEO_DIR / "drinking_pools.kml"
BASINS = DATA_GEO_DIR / "ranwell_dem_basins_prototype.geojson"
# The vp2 frame the shared transform is fitted on. Any vp2 frame would do -
# phase-correlating every one of them against this frame returns (0, 0) px -
# and this one is named because it is the frame the twin test was run on.
VP2_REFERENCE_FRAME = "site24-3-2021m.png"


def main() -> int:
    import argparse                                          # noqa: PLC0415
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase", type=int, default=None,
                    help="run one phase only (8 flood read, 9 Delta, 10 slack-edge classifier, 11 change detection, 12 predicted extent + datum test, 13 flooded extent)")
    ap.add_argument("--date", action="append", default=None,
                    help="restrict phase 8 to this frame date; repeatable")
    ap.add_argument("--mode", choices=("step", "equilibrium"), default="step",
                    help="phase 12: 'step' predicts one month ahead and is "
                         "structurally blind to the datum; 'equilibrium' uses "
                         "the level recent climate sustains, which is not")
    ap.add_argument("--z-b", dest="z_b", default="",
                    help="phase 13: the estuary boundary level, m AOD "
                         "(default ESTUARY_LEVEL_M_AOD)")
    ap.add_argument("--datums", default="",
                    help="phase 12: comma-separated datum sweep, metres")
    ap.add_argument("--wet", default=None,
                    help="phase 11: the wet date of the pair")
    ap.add_argument("--dry", action="append", default=None,
                    help="phase 11: a dry reference date; repeatable. Give two "
                         "--dry and no --wet for the dry-against-dry control")
    ap.add_argument("--shift", type=int, default=3,
                    help="phase 11: alignment search, in grid cells either way")
    ap.add_argument("--series", choices=("vp2", "tiles"), default="vp2",
                    help="which imagery the flood read uses. 'tiles' is the "
                         "PRIMARY read (2026-09-12 captures, per-cell median "
                         "near 1.0 m/px); 'vp2' is the sensitivity check at "
                         "2.884 m/px. Artefacts are kept apart by a _tiles tag "
                         "so neither overwrites the other.")
    ap.add_argument("--force-read", dest="force_read", action="store_true",
                    help="phase 8: read a frame whose own Otsu split is above "
                         "the gate. For frames whose water is specular and so "
                         "defeats a darkness test; every row written is "
                         "flagged forced")
    ap.add_argument("--form", choices=("elevation", "depth"),
                    default="elevation",
                    help="how the water table is interpolated. 'elevation' "
                         "interpolates ground+h and flattens the mound; "
                         "'depth' interpolates h alone and takes the topography "
                         "from the DEM, which is the variable the SSM is "
                         "written in")
    ap.add_argument("--kml", action="store_true",
                    help="phase 13: also write the model's predicted flood as "
                         "KML per date, to be opened in Google Earth on that "
                         "date's own imagery and judged there")
    ap.add_argument("--months", type=int, default=0,
                    help="phase 14: compute only the first N months of each "
                         "basis. For smoke-testing the phase; a partial series "
                         "is never an artefact.")
    ap.add_argument("--frames", action="store_true",
                    help="phase 14: render one map per month into "
                         "W94_frames/ for an animation. Adds several minutes "
                         "and about 60 MB; the frames are working files, not "
                         "artefacts, and are not committed.")
    ap.add_argument("--basis", choices=("both", "panel", "all"), default="both",
                    help="phase 14: which series to compute. 'panel' is the "
                         "fixed-composition headline, 'all' the longer "
                         "all-available sensitivity, 'both' the pair.")
    ap.add_argument("--cut-z", dest="cut_z", type=float, default=None,
                    help="phase 8: cut at this z instead of the frame's own "
                         "Otsu split, and write to a _fixedz set of its own. "
                         "The threshold an ACCEPTED wet frame set, applied to a "
                         "dry frame, is how a false-wet feature is identified "
                         "(D-167)")
    ap.add_argument("--mask-min-dates", dest="mask_min_dates", type=int,
                    default=FALSE_WET_MIN_DATES,
                    help="phase 19: 1 unions the dry reads; 2 keeps only what "
                         "is dark on two of them")
    ap.add_argument("--pf-mode", dest="pf_mode", choices=("C", "both"),
                    default="both",
                    help="phase 18: C for the climatological map alone; both "
                         "runs Mode V against the imagery and the dry controls")
    ap.add_argument("--sens", action="store_true",
                    help="phase 18: vary the IDW power and report the spread in "
                         "d and in area, which is the dominant uncertainty")
    ap.add_argument("--calibrate", action="store_true",
                    help="phase 8: report the open-dune z at wet and dry wells "
                         "and write W94_08_calibration.csv, writing no result")
    args = ap.parse_args()

    banner("W94 step 1 — the warren mask by frame date", __version__)
    if args.phase == 8:
        return phase8(dates=args.date, calibrate=args.calibrate,
                      series=args.series, force_read=args.force_read,
                      cut_z=args.cut_z)
    if args.phase == 10:
        return phase10(dates=args.date, calibrate=args.calibrate)
    if args.phase == 11:
        return phase11(wet=args.wet, dry=args.dry, shift=args.shift,
                       series=args.series)
    if args.phase == 19:
        return phase19(min_dates=args.mask_min_dates,
                       cut_z=(args.cut_z if args.cut_z is not None
                              else FALSE_WET_CUT_Z))
    if args.phase == 18:
        return phase18(mode=args.pf_mode, sens=args.sens)
    if args.phase == 17:
        return phase17()
    if args.phase == 16:
        return phase16(date=(args.date[0] if args.date else "2021-03-24"),
                       series=args.series)
    if args.phase == 15:
        return phase15(depths=([x for x in args.datums.split(",")]
                              if args.datums else None))
    if args.phase == 14:
        return phase14(frames=args.frames, basis=args.basis,
                       months=args.months)
    if args.phase == 13:
        return phase13(dates=args.date,
                       z_b=(float(args.z_b) if args.z_b else None),
                       kml=args.kml, form=args.form)
    if args.phase == 12:
        return phase12(dates=args.date,
                       datums=([float(x) for x in args.datums.split(",")]
                               if args.datums else None),
                       mode=args.mode)
    if args.phase == 9:
        return phase9()
    if args.phase is not None:
        warn(f"--phase {args.phase} is not separable; phases 1-7 run together")
        return 1

    phase(1, "Canopy closure, derived from the committed Script 41 index")
    info(f"a block is canopy once its index reaches {CANOPY_CLOSURE_RATIO} of the "
         f"same-frame forest control, applied monotonically")
    closures = closure_dates()
    cdf = pd.DataFrame(
        [{"block": b,
          "canopy_from": "" if d is None else str(pd.Timestamp(d).date()),
          "open_throughout": d is None}
         for b, d in sorted(closures.items())])
    p = OUT / "W94_01_canopy_closure.csv"
    cdf.to_csv(p, index=False)
    saved(p.name)

    phase(2, "Warren and canopy area, per frame date")
    man = pd.read_csv(MANIFEST, float_precision="round_trip")
    dates = sorted(set(man["imagery_date"].astype(str)))
    rows = []
    for d in dates:
        w, c = warren_on(d, closures), canopy_on(d, closures)
        rows.append({"imagery_date": d,
                     "warren_ha": round(w.area / 1e4, 3),
                     "canopy_ha": round(c.area / 1e4, 3),
                     "frames": int((man["imagery_date"].astype(str) == d).sum())})
    adf = pd.DataFrame(rows)
    p = OUT / "W94_02_warren_area_by_date.csv"
    adf.to_csv(p, index=False)
    saved(p.name)
    step(f"warren spans {adf['warren_ha'].min():.1f} to "
         f"{adf['warren_ha'].max():.1f} ha across {len(adf)} frame date(s) — "
         f"a {adf['warren_ha'].max() - adf['warren_ha'].min():.1f} ha swing, "
         f"which is the canopy changing, not the boundary")

    phase(3, "The warren polygon, once per canopy epoch")
    # One geometry per DISTINCT mask, not per date: sixteen dates collapse to a
    # handful of states, and writing sixteen identical polygons would invite a
    # reader to think they differ.
    epochs, seen = [], {}
    for d in dates:
        key = round(warren_on(d, closures).area, 3)
        if key not in seen:
            seen[key] = d
            epochs.append(d)
    info(f"{len(epochs)} distinct canopy state(s) across {len(dates)} date(s): "
         f"{', '.join(epochs)}")
    g = gpd.GeoDataFrame(
        {"epoch_from": epochs,
         "warren_ha": [round(warren_on(d, closures).area / 1e4, 3) for d in epochs]},
        geometry=[warren_on(d, closures) for d in epochs], crs=OSGB)
    # OVERWRITE BY TRUNCATION, NEVER BY UNLINK. A GDAL driver replaces an
    # existing file by deleting it first, and the desktop-bridge mount refuses
    # unlink — so a re-run fails with PermissionError on a file the first run
    # wrote. Writing the bytes ourselves truncates in place and works on both.
    p = OUT / "W94_03_warren_epochs.geojson"
    p.write_text(g.to_crs(OSGB).to_json(), encoding="utf-8")
    saved(p.name)
    p = OUT / "W94_03_warren_epochs.kml"
    tmp = Path(tempfile.mkdtemp()) / "epochs.kml"
    g.to_crs("EPSG:4326").to_file(tmp, driver="KML")
    p.write_bytes(tmp.read_bytes())
    shutil.rmtree(tmp.parent, ignore_errors=True)
    saved(p.name)

    phase(4, "Which DEM basins lie in the warren")
    if not BASINS.is_file():
        warn(f"{BASINS.name} not found — basin attribution skipped")
        return 0
    b = gpd.read_file(BASINS).to_crs(OSGB)
    latest = warren_on(dates[-1], closures)
    earliest = warren_on(dates[0], closures)
    rows = []
    with rasterio.open(DATA_DEM) as dem:
        px = dem.res[0] * dem.res[1]
        for i, row in b.iterrows():
            geom = row.geometry
            try:
                a, _ = rio_mask(dem, [geom], crop=True, filled=False)
                v = a[0].compressed()
            except Exception as exc:                       # noqa: BLE001
                warn(f"basin {i}: DEM read failed ({exc})")
                continue
            if v.size < 50:
                continue
            floor = float(np.percentile(v, 1))
            rows.append({
                "basin": row.get("basin", i),
                "area_ha": round(geom.area / 1e4, 3),
                "floor_m": round(floor, 3),
                "in_warren_earliest_pct": round(
                    100.0 * geom.intersection(earliest).area / geom.area, 1),
                "in_warren_latest_pct": round(
                    100.0 * geom.intersection(latest).area / geom.area, 1),
                "ha_below_floor_plus_0_1": round((v <= floor + 0.1).sum() * px / 1e4, 3),
                "ha_below_floor_plus_0_2": round((v <= floor + 0.2).sum() * px / 1e4, 3),
                "ha_below_floor_plus_0_5": round((v <= floor + 0.5).sum() * px / 1e4, 3),
            })
    bdf = pd.DataFrame(rows)
    p = OUT / "W94_04_basin_warren_sensitivity.csv"
    bdf.to_csv(p, index=False)
    saved(p.name)
    if len(bdf):
        r2 = (bdf["ha_below_floor_plus_0_2"] / bdf["ha_below_floor_plus_0_1"]).replace(
            [np.inf, -np.inf], np.nan).dropna()
        r5 = (bdf["ha_below_floor_plus_0_5"] / bdf["ha_below_floor_plus_0_1"]).replace(
            [np.inf, -np.inf], np.nan).dropna()
        step(f"extent sensitivity, median over {len(r2)} basin(s): "
             f"+0.2 m gives {r2.median():.2f}x the area of +0.1 m, "
             f"+0.5 m gives {r5.median():.2f}x")
        info("this is why D-159 scores flooding PER SLACK and treats area as "
             "secondary: a 0.1 m level error moves the area by about half, and "
             "the DEM's own sd is 0.145 m")
    phase(5, "Map — the basins on the warren, by epoch")
    import matplotlib.pyplot as plt                          # noqa: PLC0415
    from matplotlib.patches import Patch                     # noqa: PLC0415

    from utils.config import (SITE_MAP_EAST_MAX, SITE_MAP_EAST_MIN,
                              SITE_MAP_NORTH_MAX, SITE_MAP_NORTH_MIN)
    from utils.map_utils import add_en_axes, load_dem_hillshade
    from utils.render_utils import apply_house_style, render_figure

    apply_house_style()
    fig, ax = plt.subplots(figsize=(8.6, 7.4))
    load_dem_hillshade(ax, DATA_GEO_DIR, alpha=0.55)

    # The warren at its LARGEST and SMALLEST, so the canopy swing is the thing
    # the eye picks up rather than a single outline that looks definitive.
    first, last = epochs[0], epochs[-1]
    w_first, w_last = warren_on(first, closures), warren_on(last, closures)
    c_first, c_last = canopy_on(first, closures), canopy_on(last, closures)
    site = w_last.union(c_last)
    w_ref = warren_on('2021-03-24', closures)   # the strongest flood date

    # Draw what is EXCLUDED, not what is included. The question this map answers
    # is "which basins can be read from the air", and the eye answers it faster
    # from the canopy than from a warren fill that the basins would sit on top of.
    gpd.GeoSeries([c_last.intersection(site)], crs=OSGB).plot(
        ax=ax, facecolor="#4d7c4d", edgecolor="#2f4f2f", alpha=0.45, linewidth=0.6,
        zorder=2)
    # Ground that was OPEN in the first frame and canopy by the last — the 1998
    # replant closing. This is the part a static forest mask would get wrong.
    closing = c_last.difference(c_first).intersection(site)
    if not closing.is_empty:
        gpd.GeoSeries([closing], crs=OSGB).plot(
            ax=ax, facecolor="#c7e9c0", edgecolor="#2f4f2f", alpha=0.85,
            linewidth=0.6, hatch="///", zorder=3)
    # Ground that was canopy in the first frame and open by the last — the 2017
    # clearfell, which inverts.
    opening = c_first.difference(c_last).intersection(site)
    if not opening.is_empty:
        gpd.GeoSeries([opening], crs=OSGB).plot(
            ax=ax, facecolor="#fdae6b", edgecolor="#a63603", alpha=0.9,
            linewidth=0.6, hatch="\\\\", zorder=3)

    gpd.GeoSeries([w_last], crs=OSGB).plot(
        ax=ax, facecolor="none", edgecolor="#08519c", linewidth=1.3, zorder=5)
    b.plot(ax=ax, facecolor="none", edgecolor="#d94801", linewidth=1.6, zorder=6)
    for _, row in b.iterrows():
        c = row.geometry.representative_point()
        share = (100.0 * row.geometry.intersection(w_last).area / row.geometry.area)
        ax.annotate(f"{row.get('basin', '?')}\n{share:.0f}%",
                    (c.x, c.y), ha="center", va="center", fontsize=8, zorder=7,
                    bbox=dict(boxstyle="round,pad=0.18", fc="white",
                              ec="#d94801", lw=0.6, alpha=0.9))

    ax.set_xlim(SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX)
    ax.set_ylim(SITE_MAP_NORTH_MIN, SITE_MAP_NORTH_MAX)
    add_en_axes(ax, apply_extent=False)
    handles = [
        Patch(facecolor="#4d7c4d", edgecolor="#2f4f2f", alpha=0.45,
              label=f"canopy at {last} — excluded"),
        Patch(facecolor="#c7e9c0", edgecolor="#2f4f2f", hatch="///",
              label=f"open in {first}, canopy by {last} (1998 replant closing)"),
        Patch(facecolor="#fdae6b", edgecolor="#a63603", hatch="\\\\",
              label=f"canopy in {first}, open by {last} (2017 clearfell)"),
        Patch(facecolor="none", edgecolor="#08519c", linewidth=1.3,
              label=f"warren at {last} ({w_last.area / 1e4:.0f} ha; "
                    f"{w_first.area / 1e4:.0f} ha at {first})"),
        Patch(facecolor="none", edgecolor="#d94801", linewidth=1.6,
              label="DEM basin (label: % in the warren)"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=7.5, framealpha=0.92)
    ax.set_title("W94 — which DEM basins can be read from the air\n"
                 "canopy excluded by frame date; the hatched blocks are the ground "
                 "a static forest mask would get wrong")
    p = OUT / "W94_05_basins_on_warren.png"
    render_figure(fig, p)
    saved(p.name)

    phase(6, "Slacks — closed depressions in the DEM")
    from scipy import ndimage as ndi                         # noqa: PLC0415
    from rasterio.features import geometry_mask, shapes      # noqa: PLC0415
    from shapely.geometry import shape as shapely_shape      # noqa: PLC0415

    from utils.config import SLACK_MIN_AREA_M2, SLACK_MIN_DEPTH_M
    from utils.slacks import leaf_ids, merge_tree

    with rasterio.open(DATA_DEM) as dem_src:
        db = dem_src.bounds
        want = site.bounds
        # CLAMP TO THE RASTER. `site` is the warren UNION the canopy, and the
        # forest block runs well outside both the site boundary and the DEM
        # footprint — asking for its bounds gives a window partly off the raster,
        # which rasterio serves without complaint and which silently misplaces
        # every cell. Measured while this was wrong: the warren came back as
        # 104.5 ha of the window instead of 656.9, and the slack count in the
        # warren fell from 167 to 31.
        read_b = (max(want[0], db.left), max(want[1], db.bottom),
                  min(want[2], db.right), min(want[3], db.top))
        if read_b != want:
            info("the requested window runs outside the DEM (the forest block "
                 "does); clamped to the raster footprint")
        win = rasterio.windows.from_bounds(*read_b, dem_src.transform)
        arr = dem_src.read(1, window=win).astype("float32")
        tr = dem_src.window_transform(win)
        cell = abs(tr.a * tr.e)
    info(f"site window {arr.shape[1]} x {arr.shape[0]} cells at {abs(tr.a):.0f} m")
    # The warren must be essentially inside the window, or every count below is
    # measured against the wrong ground.
    _wm_check = geometry_mask([w_ref], out_shape=arr.shape, transform=tr,
                              invert=True)
    _cover = 100.0 * _wm_check.sum() * cell / w_ref.area
    if _cover < 99.0:
        warn(f"only {_cover:.1f} % of the warren falls inside the DEM window — "
             f"the slack counts below are measured against the wrong ground. "
             f"Fix the window before reading anything from them.")
    else:
        info(f"{_cover:.1f} % of the warren is inside the window")
    # THE MERGE TREE, not a fixed-depth labelling: slacks merge as the level
    # rises (Martin, 2026-09-11), so the unit is a node of a hierarchy and a
    # level, never a static polygon.
    leaf, nodes = merge_tree(arr)
    leaves = leaf_ids(nodes)
    by_id = {n["id"]: n for n in nodes}
    Nn = len(nodes)
    par = np.fromiter((nd["parent"] for nd in nodes), dtype=np.int64, count=Nn)
    depth_a = np.fromiter(((nd["merge_level_m"] - nd["floor_m"])
                           if nd["parent"] != -1 else -1.0 for nd in nodes),
                          dtype=float, count=Nn)
    area_a = np.fromiter((nd["cells"] * cell for nd in nodes),
                         dtype=float, count=Nn)
    open_a = np.fromiter((nd["open"] for nd in nodes), dtype=bool, count=Nn)

    # A LEAF IS NOT A SLACK. There are a quarter of a million local minima in
    # this DEM and they are pinholes: taking leaves as the unit gave 87 in the
    # warren and none above 500 m2. The slack is the LARGEST node on each branch
    # that still holds water — qualifying, with no qualifying ancestor.
    qual = (~open_a) & (depth_a > SLACK_MIN_DEPTH_M) & (area_a >= SLACK_MIN_AREA_M2)
    idx = np.arange(Nn, dtype=np.int64)
    jump = np.where(par < 0, idx, par)
    cur, anc = jump.copy(), qual[jump].copy()
    for _ in range(64):
        nxt = jump[cur]
        if (nxt == cur).all():
            break
        cur = nxt
        anc |= qual[cur]
    maximal = qual & ~anc
    sdf = pd.DataFrame([
        {"slack": int(i), "cells": by_id[int(i)]["cells"],
         "area_m2": float(area_a[i]), "floor_m": float(by_id[int(i)]["floor_m"]),
         "spill_m": float(by_id[int(i)]["merge_level_m"]),
         "depth_m": float(depth_a[i])}
        for i in np.flatnonzero(maximal)])
    info(f"merge tree: {Nn} node(s), {len(leaves)} local minima; "
         f"{int(qual.sum())} qualify at depth > {SLACK_MIN_DEPTH_M} m and "
         f">= {SLACK_MIN_AREA_M2:.0f} m2, of which {len(sdf)} are maximal on "
         f"their branch — those are the slacks")
    # Rasterise the kept slacks: a cell belongs to the kept ANCESTOR of its leaf.
    keep_set = set(sdf["slack"])
    # Map every node to its kept ancestor by POINTER JUMPING, then index the
    # leaf raster through it. Two earlier drafts were too slow to finish: a loop
    # over 264k leaf labels against 3.8M cells (10^12 comparisons), and a Python
    # chain-walk over all 516k nodes. This is a handful of vectorised passes.
    N = len(nodes)
    par = np.fromiter((nd["parent"] for nd in nodes), dtype=np.int64, count=N)
    idx = np.arange(N, dtype=np.int64)
    par = np.where(par < 0, idx, par)                 # roots point at themselves
    res = np.full(N, -1, dtype=np.int64)
    for k in keep_set:
        res[k] = k
    jump = par.copy()
    for _ in range(64):
        todo = (res < 0) & (jump != idx)
        if not todo.any():
            break
        res[todo] = res[jump[todo]]
        jump = jump[jump]
    lut = np.zeros(N + 1, dtype="int32")
    lut[:N] = np.where(res < 0, 0, res)
    lab = lut[leaf]

    # In the warren, and gauged or not — the two facts that decide whether a
    # slack can be READ from the air and whether the network already reports it.
    wmask = geometry_mask([w_ref], out_shape=arr.shape, transform=tr, invert=True)
    in_warren = {int(v) for v in np.unique(lab[wmask & (lab > 0)])}
    wells = pd.read_csv(REPO / "outputs" / "01_well_elevations.csv",
                        float_precision="round_trip")
    inv = ~tr
    # HYDRAULIC ATTACHMENT, not a distance. A well belongs to the slack whose
    # depression contains it in the hierarchy, and it becomes wet when the level
    # reaches its OWN ground — which is what an edge-sited well is (Martin,
    # 2026-09-10: sited at slack edges for ease of measurement). No metres to
    # choose, and `nearest_well_m` stays for wells no depression reaches.
    gauged, wet = {}, {}
    for _, r in wells.iterrows():
        col, row = inv * (r["E"], r["N"])
        col, row = int(col), int(row)
        if 0 <= row < lab.shape[0] and 0 <= col < lab.shape[1]:
            lv = int(lab[row, col])
            if lv:
                gauged.setdefault(lv, []).append(str(r["Name"]))
                wet.setdefault(lv, []).append(round(float(arr[row, col]), 2))
    sdf["in_warren"] = sdf["slack"].isin(in_warren)
    sdf["wells_inside"] = sdf["slack"].map(lambda k: ";".join(gauged.get(k, [])))
    sdf["wells_wet_at_m"] = sdf["slack"].map(
        lambda k: ";".join(str(v) for v in wet.get(k, [])))
    # POINT-IN-POLYGON IS THE WRONG JOIN HERE, and the record says why: wells
    # were sited at slack EDGES for ease of measurement (Martin, 2026-09-10;
    # CEH1, CEH9 and NW6 named). Measured: only 37 of 99 wells fall inside a
    # warren slack, the median well sits 13.6 m from the nearest one, and 52 are
    # within 20 m. So "contains a well" undercounts the gauged slacks badly.
    # The distance is written out and the THRESHOLD IS NOT CHOSEN HERE — it is a
    # design call, and baking one in would fix a headline count by fiat.
    sdf["area_ha"] = (sdf["area_m2"] / 1e4).round(4)
    for c in ("floor_m", "spill_m", "depth_m"):
        sdf[c] = sdf[c].round(3)
    # Nearest well to each slack, recorded rather than thresholded.
    #
    # POLYGONISE ONLY WHAT IS USED. The tree keeps thousands of slacks, most of
    # them a handful of cells, and vectorising every one then dissolving was the
    # step that would not finish. Polygons are built for slacks in the warren at
    # or above POLY_MIN_AREA_M2; the CSV keeps them all, so nothing is lost that
    # a later step cannot recover.
    from shapely.geometry import Point                       # noqa: PLC0415
    keep_ids = set(sdf.loc[sdf["in_warren"], "slack"])
    info(f"polygonising {len(keep_ids)} slack(s) that touch the warren; "
         f"the CSV keeps all {len(sdf)}")
    keep_arr = np.zeros(len(nodes) + 1, dtype=bool)
    for k in keep_ids:
        keep_arr[k] = True
    poly_lab = np.where(keep_arr[lab], lab, 0).astype("int32")
    polys0, ids0 = [], []
    for geom, val in shapes(poly_lab, mask=(poly_lab > 0), transform=tr):
        polys0.append(shapely_shape(geom))
        ids0.append(int(val))
    sg0 = gpd.GeoDataFrame({"slack": ids0}, geometry=polys0, crs=OSGB)
    sg0 = sg0.dissolve(by="slack", as_index=False)

    # CLIP TO READABLE GROUND, and drop what no longer qualifies (Martin,
    # 2026-09-11: "exclude the lake and the shore"). Two independent failure
    # modes, each catching what the other misses:
    #   * LLYN RHOS-DDU is permanent open water, not a flooded slack. It came
    #     through as a 5.41 ha depression, floor 7.28 m. Counting it as a true
    #     positive is the error that keeping the lake gauge out of the 88
    #     dipwells exists to prevent.
    #   * THE SHORE. Eighteen "slacks" sat below 1 m AOD, 7.4 ha, including a
    #     4.96 ha striped feature at -1.52 m — wet intertidal sand in the LiDAR.
    #     They survived because a depression only had to TOUCH the warren.
    # Clipping strictly to the warren and subtracting the lake removes both
    # without an elevation threshold to argue about.
    from utils.config import SLACK_LAKE_OVERLAP_FRAC, SLACK_MIN_FLOOR_M
    lake = _features("Llyn Rhos Ddu")
    before_n, before_ha = len(sg0), sg0.area.sum() / 1e4
    sg0["geometry"] = sg0.geometry.intersection(w_ref)
    sg0 = sg0[~sg0.geometry.is_empty].copy()
    n_clip = len(sg0)
    # The lake, by overlap fraction rather than subtraction.
    frac = sg0.geometry.intersection(lake).area / lake.area
    is_lake = frac.fillna(0) >= SLACK_LAKE_OVERLAP_FRAC
    sg0 = sg0[~is_lake]
    n_lake = int(is_lake.sum())
    # The shore, by floor elevation.
    floors = dict(zip(sdf["slack"], sdf["floor_m"]))
    on_shore = sg0["slack"].map(floors) < SLACK_MIN_FLOOR_M
    sg0 = sg0[~on_shore]
    n_shore = int(on_shore.sum())
    sg0 = sg0[sg0.area >= SLACK_MIN_AREA_M2].copy()
    info(f"clipped to the warren: {before_n} -> {n_clip}; "
         f"lake removed {n_lake}; shore (floor < {SLACK_MIN_FLOOR_M} m) removed "
         f"{n_shore}; {len(sg0)} slack(s) remain, "
         f"{before_ha:.1f} -> {sg0.area.sum() / 1e4:.1f} ha")
    # THE HOLLOW IS NOT THE SLACK, and conflating them is what put a ridge
    # inside a mapped "slack" near CEH32 (Martin, 2026-09-11). `sg0` is the
    # node's extent - everything that drains to the floor, up to the spill - so
    # it answers "which depression does this belong to". It does NOT answer
    # "what is under water", because the node is drawn to its spill while the
    # criterion is a depth. The wet surface is the cells at or below
    # floor + SLACK_MIN_DEPTH_M, and it is a different polygon: at the CEH32
    # node, 0.01 ha of 5.60. Both are emitted, named differently, and the maps
    # and the scoring each take the one they mean.
    floor_lut = np.zeros(len(nodes) + 1, dtype="float64")
    floor_lut[:] = np.inf
    for _k, _f in zip(sdf["slack"], sdf["floor_m"]):
        floor_lut[int(_k)] = float(_f)
    wet_cells = (lab > 0) & (arr <= floor_lut[lab] + SLACK_MIN_DEPTH_M)
    wet_lab = np.where(wet_cells & keep_arr[lab], lab, 0).astype("int32")
    wpolys, wids = [], []
    for geom, val in shapes(wet_lab, mask=(wet_lab > 0), transform=tr):
        wpolys.append(shapely_shape(geom))
        wids.append(int(val))
    sw0 = gpd.GeoDataFrame({"slack": wids}, geometry=wpolys, crs=OSGB)
    sw0 = sw0.dissolve(by="slack", as_index=False)
    sw0["geometry"] = sw0.geometry.intersection(w_ref)
    sw0 = sw0[~sw0.geometry.is_empty].copy()
    sw0 = sw0[sw0["slack"].isin(set(sg0["slack"]))].copy()
    _wet = dict(zip(sw0["slack"], sw0.area))
    sdf["wet_area_m2"] = sdf["slack"].map(_wet)
    sdf["wet_area_ha"] = (sdf["wet_area_m2"] / 1e4).round(4)
    _hol = dict(zip(sg0["slack"], sg0.area))
    sdf["wet_frac"] = (sdf["slack"].map(_wet)
                       / sdf["slack"].map(_hol)).round(3)
    _hw, _ww = sg0.area.sum() / 1e4, sw0.area.sum() / 1e4
    step(f"hollows {len(sg0)}, {_hw:.1f} ha drawn to their spill; "
         f"WET at floor + {SLACK_MIN_DEPTH_M * 100:.0f} cm, {_ww:.1f} ha "
         f"({100 * _ww / _hw:.1f} % of the drawn area) across {len(sw0)} "
         f"slack(s). THE SECOND NUMBER IS THE ONE THAT FLOODS.")

    # The clipped area is the one that counts, so it replaces the tree's.
    clipped = dict(zip(sg0["slack"], (sg0.area / 1e4).round(4)))
    sdf["area_ha_clipped"] = sdf["slack"].map(clipped)
    sdf["readable"] = sdf["slack"].isin(set(sg0["slack"]))
    wpts = gpd.GeoDataFrame(
        {"well": wells["Name"].astype(str)},
        geometry=[Point(x, y) for x, y in zip(wells["E"], wells["N"])], crs=OSGB)
    near = gpd.sjoin_nearest(sg0, wpts, how="left", distance_col="nearest_well_m")
    near = (near.sort_values("nearest_well_m")
                .drop_duplicates("slack")[["slack", "well", "nearest_well_m"]]
                .rename(columns={"well": "nearest_well"}))
    near["nearest_well_m"] = near["nearest_well_m"].round(1)
    sdf = sdf.merge(near, on="slack", how="left")

    p = OUT / "W94_06_slacks.csv"
    sdf.sort_values("area_m2", ascending=False).to_csv(p, index=False)
    saved(p.name)

    inw = sdf[sdf["in_warren"]]
    step(f"{len(inw)} slack(s) in the warren at or above {SLACK_MIN_AREA_M2:.0f} m2")
    for cut in (500.0, 1000.0, 5000.0):
        c = inw[inw["area_m2"] >= cut]
        if len(c):
            info(f"  >= {cut:6.0f} m2 : {len(c):4d} slack(s), median "
                 f"{c['area_ha'].median():.3f} ha, "
                 f"{int(c['wells_inside'].astype(bool).sum()):3d} contain a well")
    _nw = sdf.loc[sdf["readable"], "nearest_well_m"].dropna()
    info(f"HOW MANY ARE UNGAUGED DEPENDS ON THE ATTACHMENT RULE, which is not "
         f"decided here: of {len(wells)} wells, "
         f"{int(sdf['wells_inside'].astype(bool).sum())} readable slack(s) "
         f"contain one; slack-to-nearest-well is "
         f"{(_nw <= 0).sum()} at 0 m, {(_nw <= 20).sum()} within 20 m and "
         f"{(_nw <= 50).sum()} within 50 m of {len(_nw)}. Wells were sited at "
         f"slack EDGES, so `nearest_well_m` is written per slack and the cut is "
         f"made later, in the open.")
    info(f"for comparison the Ranwell prototype basins run "
         f"{bdf['area_ha'].min():.1f} to {bdf['area_ha'].max():.1f} ha — "
         f"catchment scale, which is why they are not the scoring unit")
    info("AREA IS NOT FILTERED BY WHAT A FRAME CAN SEE. The slack map is a "
         "property of the ground; CANOPY_FLOOD_MIN_PATCH_PX is applied per "
         "frame at scoring time, so the ground truth does not depend on which "
         "photographs happen to exist.")

    _attrs = ["slack", "area_ha", "floor_m", "spill_m", "depth_m",
              "in_warren", "readable", "area_ha_clipped", "wet_area_ha",
              "wet_frac", "wells_inside", "wells_wet_at_m", "nearest_well",
              "nearest_well_m"]
    # THE HOLLOW — the node extent, floor to spill. The ATTRIBUTION unit: which
    # depression a flood body belongs to. Never an area that floods.
    sh = sg0.merge(sdf[_attrs], on="slack", how="left")
    # THE SLACK — the surface at floor + SLACK_MIN_DEPTH_M. The WET area: what a
    # photograph is compared with, and what is recognised on the ground.
    sg = sw0.merge(sdf[_attrs], on="slack", how="left")
    for _name, _gdf, _stem in (("hollows", sh, "W94_06_hollows"),
                               ("slacks", sg, "W94_06_slacks")):
        q = OUT / f"{_stem}.geojson"
        q.write_text(_gdf.to_json(), encoding="utf-8")
        saved(q.name)
        tmp = Path(tempfile.mkdtemp()) / f"{_name}.kml"
        _gdf.to_crs("EPSG:4326").to_file(tmp, driver="KML")
        q = OUT / f"{_stem}.kml"
        q.write_bytes(tmp.read_bytes())
        shutil.rmtree(tmp.parent, ignore_errors=True)
        saved(q.name)

    phase(7, "Map — the slacks, for recognition on the ground")
    fig2, ax2 = plt.subplots(figsize=(11.5, 9.8))
    load_dem_hillshade(ax2, DATA_GEO_DIR, alpha=0.6)
    gpd.GeoSeries([w_ref], crs=OSGB).plot(ax=ax2, facecolor="none",
                                          edgecolor="#08519c", lw=1.0, zorder=3)
    # The hollow is drawn as an OUTLINE and the wet surface as the fill, so the
    # difference between them is visible on the map rather than collapsed into
    # one blue polygon — the collapse that made a ridge read as slack.
    sh.plot(ax=ax2, facecolor="none", edgecolor="#6baed6", lw=0.4, zorder=3.5)
    sg.plot(ax=ax2, facecolor="#2171b5", edgecolor="#08306b", lw=0.35,
            alpha=0.85, zorder=4)
    wpts.plot(ax=ax2, color="#d94801", markersize=8, zorder=5)
    joined = gpd.sjoin(wpts, sh[["slack", "geometry"]], how="inner",
                       predicate="within")
    for _, r in joined.iterrows():
        ax2.annotate(r["well"], (r.geometry.x, r.geometry.y), fontsize=6,
                     xytext=(3, 3), textcoords="offset points", zorder=6,
                     color="#7f2704")
    sg_area = sh.assign(ha=sh.area / 1e4)
    for _, r in sg_area.nlargest(14, "ha").iterrows():
        c = r.geometry.representative_point()
        ax2.annotate(f"{r['ha']:.1f} ha", (c.x, c.y), fontsize=6, ha="center",
                     va="center", zorder=7, color="white")
    ax2.set_xlim(SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX)
    ax2.set_ylim(SITE_MAP_NORTH_MIN, SITE_MAP_NORTH_MAX)
    add_en_axes(ax2, apply_extent=False)
    ax2.set_title(
        f"W94 — slacks in the warren: WET area under "
        f"{SLACK_MIN_DEPTH_M * 100:.0f} cm of water (solid), inside the hollow "
        f"that holds it (outline)\n{len(sh)} hollows, "
        f"{sh.area.sum() / 1e4:.0f} ha drawn to their spill; wet "
        f"{sg.area.sum() / 1e4:.1f} ha; lake and shore excluded; wells orange, "
        f"hollows labelled by their own area")
    p = OUT / "W94_07_slacks.png"
    render_figure(fig2, p)
    saved(p.name)

    info("the repeat-floor drift test is NOT run here — it needs digitised "
         "outlines on two dates, which do not exist yet. See the module "
         "docstring.")
    return 0


def _m41_module():
    """Script 41 as a module. The tile read needs its `_homography`,
    `_sample_to_grid` and `_frame_window` and none of its registration, so it is
    imported without the two-minute marker detection `_vp2_transform` pays for.
    """
    import importlib.util                                    # noqa: PLC0415
    spec = importlib.util.spec_from_file_location(
        "m41", str(REPO / "src" / "41_canopy_cover.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _vp2_transform():
    """The vp2 homography, cached as CONTROL POINTS rather than as a function.

    Registration costs about two minutes — `_register_all` detects markers on
    every registration frame in the manifest — and phase 8 needs it on every
    run. The cache is `W94_08_vp2_control.csv`: the well positions and their
    fitted pixel coordinates, from which `_homography` refits the same eight
    parameters exactly (measured: 2.4e-10 px maximum disagreement). A table of
    correspondences is auditable in a way a pickled closure is not, and it is
    the evidence for the fit rather than the fit itself.

    ONE TRANSFORM SERVES EVERY vp2 FRAME. Measured 2026-09-11: phase-correlating
    every vp2 frame against `site24-3-2021.png` returns (0, 0) px with the peak
    200-430x the noise sd, and the markers-ON twin returns r = 0.9954. That is
    what lets 2010-05-27 — the only measurement frame with no twin — be read at
    all. Note it is NOT an independent negative: it carries the same imagery as
    2011-06-19 over the warren (D-159, corrected 2026-09-12).
    """
    import importlib.util                                    # noqa: PLC0415
    from shapely.ops import unary_union                      # noqa: PLC0415
    from utils.kml_io import read_kml                        # noqa: PLC0415
    from utils.paths import INT_LOCATIONS                    # noqa: PLC0415

    spec = importlib.util.spec_from_file_location(
        "m41", str(REPO / "src" / "41_canopy_cover.py"))
    m41 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m41)

    cache = OUT / "W94_08_vp2_control.csv"
    if cache.exists():
        c = pd.read_csv(cache, float_precision="round_trip")
        info(f"vp2 transform from {cache.name} ({len(c)} control point(s))")
    else:
        info("no cached vp2 transform; registering — about two minutes")
        ctrl = unary_union(list(
            read_kml(DATA_GEO_DIR / f"{m41.CONTROL_KML}.kml").geometry))
        w = pd.read_csv(INT_LOCATIONS, float_precision="round_trip")
        ec = next(x for x in w.columns if x.lower() in ("easting", "e", "x"))
        nc = next(x for x in w.columns if x.lower() in ("northing", "n", "y"))
        E = w[ec].values.astype(float)
        N = w[nc].values.astype(float)
        man = pd.read_csv(MANIFEST, float_precision="round_trip")
        man = man[man["role"] == "registration"]
        paths = [m41.AERIAL_DIR / f for f in man["filename"]
                 if (m41.AERIAL_DIR / f).exists()]
        reg, _ = m41._register_all(paths, ctrl, E, N)
        r = reg.get(VP2_REFERENCE_FRAME)
        if r is None or r.get("fitted") is None:
            warn(f"{VP2_REFERENCE_FRAME} did not register; phase 8 cannot run")
            return None, m41
        px, py = r["fitted"](E, N)
        c = pd.DataFrame({"E": E, "N": N, "px": px, "py": py})
        c.to_csv(cache, index=False)
        saved(cache.name)
    P = np.column_stack([c["E"].values, c["N"].values,
                         c["px"].values, c["py"].values])
    H = m41._homography(P)
    u, v = H(P[:, 0], P[:, 1])
    err = float(np.max(np.hypot(u - P[:, 2], v - P[:, 3])))
    info(f"refit reproduces the cached control points to {err:.2e} px")
    return H, m41


def _clear_date(date, tag=""):
    """Remove any artefact left from an EARLIER, wider gate for this date.

    A frame that now reads DRY must not leave last run's flood polygons on
    disk: a map and a CSV that contradict the verdict beside them are exactly
    the artefact this project keeps being bitten by. The mount refuses unlink,
    so a rename into `_to_delete/` is the fallback where a delete is refused —
    the same move `working/wgit` makes for a stale git lock.
    """
    gone = []
    for stem in (f"W94_08_flood{tag}_{date}", f"W94_08_wells{tag}_{date}"):
        for ext in (".geojson", ".kml", ".png", ".csv"):
            q = OUT / f"{stem}{ext}"
            if not q.exists():
                continue
            try:
                q.unlink()
            except OSError:
                bin_ = REPO / "_to_delete"
                bin_.mkdir(exist_ok=True)
                q.rename(bin_ / f"{q.name}.superseded")
            gone.append(q.name)
    if gone:
        warn(f"  removed {len(gone)} artefact(s) from a previous, wider gate: "
             f"{', '.join(gone)}")


def _otsu(x):
    """(threshold, between-class variance as a fraction of the total).

    The FRACTION is the point. Otsu's threshold always exists; the fraction says
    whether the histogram it split was two populations or one.
    """
    x = x[np.isfinite(x)]
    if x.size < 100:
        return float("nan"), 0.0
    lo, hi = np.percentile(x, [0.5, 99.5])
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return float("nan"), 0.0
    hist, edges = np.histogram(np.clip(x, lo, hi), bins=256, range=(lo, hi))
    p = hist.astype(float) / max(hist.sum(), 1)
    mids = 0.5 * (edges[1:] + edges[:-1])
    w0 = np.cumsum(p)
    m0 = np.cumsum(p * mids)
    mt = m0[-1]
    with np.errstate(invalid="ignore", divide="ignore"):
        between = (mt * w0 - m0) ** 2 / (w0 * (1.0 - w0))
    between = np.where(np.isfinite(between), between, 0.0)
    k = int(np.argmax(between))
    total = float(np.sum(p * (mids - mt) ** 2))
    return float(mids[k]), (float(between[k] / total) if total > 0 else 0.0)


TILE_CACHE = REPO / "working" / "updates" / "crossres_transforms.json"
TILE_DIR = DATA_GEO_DIR / "slacks"
TILE_INVENTORY = REPO / "working" / "updates" / "W159_registration_inventory.csv"
# A date that does not see this much of the warren cannot carry a warren-wide
# area: a partial mosaic still yields a polygon and a number, and the number is
# not a smaller flood but an unknown one. Coverage is measured per date by
# `tools/tile_coverage.py`; this is the threshold that decides what it licenses.
# RETIRED 2026-09-13 (Martin): a covered-fraction gate asks the wrong question.
# See tools/tile_coverage.py for the reasoning; what governs now is the hollow a
# date cannot see, and the only refusal is when that bound swallows the answer.
HOLLOW_UNSEEN_MAX_FRAC = 0.10
# A cell is "the same imagery" at this tolerance — the value IDENTICAL_TOL-style
# checks elsewhere use, because a served block is bit-identical and not merely
# similar. A block smaller than the smallest thing this project calls a slack is
# coincidence, not a stale patch.
STALE_IDENTICAL_TOL = 1.0
STALE_MIN_BLOCK_M2 = 2000.0
# A floor or a rim needs enough cells for a median and a MAD to mean anything.
MIN_SLACK_CELLS = 12
# THE DRY CONTROLS, and they are the test rather than the calibration set's
# leftovers: every one has 100 % tile coverage (tools/tile_coverage.py,
# 2026-09-12) and no well at or above ground in its month. Thresholds are set
# from these and the wet dates are then read with thresholds that never saw them.
# How many noise standard deviations count as change. STATED, NOT TUNED — the
# ordinary 3 sigma — and the dry-against-dry control is what says whether it is
# enough, rather than this number being moved until an answer looks right.
CHANGE_SIGMA = 3.0
# The raster's local bias, MEASURED in phase 9 from 35 waterline/well pairs over
# three dates: the median difference between a flood body's waterline elevation
# and that well's own water surface, repeating within a well at a median sd of
# 0.018 m. Subtracted from every DEM floor, because a floor is only as good as
# the raster it is read from.
PHASE9_DEM_BIAS_M = 0.302
# WHICH FLOOD READ THE BIAS IS MEASURED FROM, pinned rather than left to whichever
# polygons happen to exist. The tiles are the higher-resolution instrument and the
# tile waterline should be the better contour, but there is ONE tile date against
# three vp2 dates, and on DGPS pairs the two bases differ by 3.2 cm (+0.302 vp2,
# +0.270 tiles) — more than any other choice in this measurement. Three dates of
# averaging beats one date of resolution until more tile dates exist, so the basis
# is vp2 and the switch is a deliberate edit here, not a side effect of a re-run.
PHASE9_WATERLINE_BASIS = "vp2"
# THE MONTHLY SERIES IS BUILT ON A FIXED PANEL. The network trebles across the
# record (a median of 7 wells reporting in 2005 against 79 from 2020), so a
# series on whatever wells exist each month cannot separate a rising water table
# from a growing dipwell network. Measured leave-one-out error of the surface
# saturates at about 55 wells - 0.613 m on 25, 0.521 on 57, 0.527 on every
# available well - so holding composition constant costs nothing. Wells qualify
# by reporting in at least this fraction of months from this start.
SERIES_PANEL_START = "2007-01"
SERIES_PANEL_MIN_COVERAGE = 0.80
# Membership is fixed from SERIES_PANEL_START, but REPORTING is not: the 57-well
# panel only reaches this share of itself in 2010-03, and reports 20-30 wells
# before that. The series is computed from the start and carries panel_frac on
# every row; this is the threshold above which months are comparable with one
# another, and it is a reporting fact about the record, not a tuning knob.
SERIES_PANEL_COMPLETE_FRAC = 0.80
# Frame rendering. The depth scale is FIXED across frames or the animation reads
# as a colour change rather than a water-level change.
SERIES_DEPTH_VMAX_M = 1.0
SERIES_FRAME_DPI = 80
SERIES_FRAME_CELL_PT = 1.4
SERIES_WATER_COLOUR = "#1f6fb4"
# The strip inset's axes. Fixed across frames for the same reason the depth
# scale would have been: a strip that rescales shows nothing moving.
SERIES_STRIP_MONTHS = 240
SERIES_STRIP_HA_MAX = 25.0
# A slack counts as observed-wet for the shortfall diagnosis when the imagery
# covers at least this share of its cells. Not a tuning knob: below it a unit is
# clipped by a water body's edge rather than being under it, and an edge cell
# says nothing about whether the slack flooded.
SHORTFALL_MIN_WET_FRAC = 0.50
# The scale over which the ground the depth form adds h to is smoothed. The
# water-table mound is a regional form; the DEM is not. 0 m collapses the
# construction (4.67 ha on the wettest date, 0.00 on every dry control) and
# 500 m and beyond loses the dry-control margin. Swept, not chosen: see phase 17.
SURFACE_GROUND_SMOOTH_M = 100.0
# WELLS WHOSE GROUND ELEVATION CAME FROM THE DEM CANNOT MEASURE THE DEM'S BIAS.
# The measurement is median(DEM along the waterline) - (ground + h). Where ground
# is itself a DEM read at the well, the raster's bias appears on both sides and
# largely cancels: the six such pairs return -0.037 m with a MAD of 0.153 against
# the 29 DGPS pairs' +0.302 at 0.083. Same principle as the scraped-well exclusion
# already applied below - a well whose ground has CHANGED since the LiDAR cannot
# measure the LiDAR, and neither can a well whose ground IS the LiDAR.
PHASE9_BIAS_GROUND_SOURCES = ("dgps",)
# The vp2 registration residual, the distance inside which a well and a slack
# cannot be told apart by the registration — the same tolerance phase 8 uses.
VP2_RESIDUAL_M = 3.93
# Below this range the datum curve is flat and says nothing. Stated before the
# sweep is run so a flat curve cannot be read as a preference.
DATUM_CURVE_MIN_SPAN = 0.02
# ── the tidal boundary (phase 13) ──────────────────────────────────────────
# The aquifer discharges to the Malltraeth estuary, so the water table is pinned
# near tide level along that margin. `moad.kml` is the line; 0 m AOD is
# approximately mean sea level and is the conservative end of the defensible
# range (a water table at a tidal margin usually sits a little ABOVE mean tide,
# towards MHW). The choice is nearly additive — measured 2026-09-13, +1 m of z_b
# adds about 3.5 ha to every date and changes no ranking — so it is stated here
# rather than tuned, and its sensitivity is reported with any area.
ESTUARY_KML = "moad"
ESTUARY_LEVEL_M_AOD = 0.0
ESTUARY_POINT_SPACING_M = 50.0
ESTUARY_REACH_M = 400.0
# The Llyn Rhos-Ddu lake gauge, which is NOT in the classified dipwell network
# and must never set the water table: it is the only point at or above ground on
# both dry controls, and its presence alone made them look wet.
LAKE_GAUGE_NAME = "llyn rhos"
MIN_WELLS_FOR_SURFACE = 10
# Below this margin over the dry-control floor, a flooded area is not worth
# quoting. Stated before the run, as FLOOD_OTSU_MAX_Z was.
DRY_CONTROL_MIN_RATIO = 3.0
# Below this, two captures of one place do not agree on ground that cannot have
# changed, so their difference measures the registration rather than the water.
# Calibrated on what a WORKING pair gives: the vp2 markers-ON/OFF twins of one
# date reach 0.994 and two different vp2 dates 0.342, while two tiles of one date
# managed 0.09 and produced a result that looked plausible and was noise.
PAIR_MIN_R = 0.20
DRY_CALIBRATION_DATES = ("2009-04-20", "2010-05-27", "2012-05-26", "2019-07-29")
# The months the imagery read covers, so the series can mark which of its rows
# are validated and which are interpolation. Derived from the read dates, not
# typed twice.
_DRY_MONTHS = {d[:7] for d in DRY_CALIBRATION_DATES}
_IMAGERY_MONTHS = _DRY_MONTHS | {"2017-03", "2020-03", "2021-03", "2021-04",
                                 "2026-03"}


def _tile_frames(date):
    """The registered tiles for one imagery date, finest first.

    INHERITED FRAMES ARE NOT INCLUDED and that is deliberate. A markers-OFF
    capture takes its twin's transform, so it adds no ground the twin does not
    already see — it would be the same pixels of the same view entering the
    mosaic twice, which is exactly the double count retiring site19-6-2011.png
    removed from the vp2 series. The twin discipline buys clean ground, not more
    of it.
    """
    if not TILE_CACHE.exists():
        return []
    import json                                              # noqa: PLC0415
    frames = json.loads(TILE_CACHE.read_text())["frames"]
    out = [(k, v) for k, v in frames.items()
           if v.get("series") == "tile" and str(v.get("date"))[:10] == date]
    return sorted(out, key=lambda kv: float(kv[1]["gsd_m"]))


def _mosaic(date, m41, EE, NN, dune_prior):
    """Composite one date's tiles onto the ground grid, finest frame winning.

    WHERE TILES OVERLAP THE BETTER FRAME IS USED, not the first or the last. The
    captures were taken at 1.0-2.3 m/px and they overlap heavily, so a mosaic
    that took whatever came last would throw away the resolution the recapture
    was for. Each cell carries the finest frame that sees it, and the `gsd`
    reported for the date is the median of those per-cell values.

    **EACH TILE IS NORMALISED AGAINST ITS OWN OPEN DUNE BEFORE COMPOSITING, and
    that is not a refinement — mosaicking raw luminance breaks the method.** Every
    Google Earth capture carries its own exposure, so a composite of six of them
    has variance BETWEEN tiles on top of the variance within each. Measured on
    2021-03-24: compositing luminance gave an open-dune MAD of 26.9 against 8.9
    to 14.2 for a single vp2 frame, which inflates sigma, compresses z toward
    zero, and pushed the frame's own Otsu threshold to -0.63 — so the wettest
    frame in the series came back DRY at the gate. The fix is to do what the
    method already says: normalise against THE FRAME'S own open dune, one frame
    at a time, and mosaic the z values. The second normalisation downstream then
    operates on a surface that has no inter-tile offset left in it, and is
    approximately the identity.

    Returns (z, ok, gsd_median, residual_median, n_frames, cells) in the same
    form `_sample_to_grid` gives for a single frame, so everything after the
    sampling step is untouched.
    """
    from PIL import Image                                    # noqa: PLC0415
    tiles = _tile_frames(date)
    if not tiles:
        return None, None, None, None, 0, 0.0
    grid = np.full(EE.shape, np.nan)
    best = np.full(EE.shape, np.inf)
    used, refused = [], []
    for name, v in tiles:
        fp = TILE_DIR / name
        if not fp.exists():
            continue
        g = float(v["gsd_m"])
        a = np.asarray(Image.open(fp).convert("RGB")).astype(float)
        lum = 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]
        H = m41._homography(np.asarray(v["pairs"], float))
        gg, ok_ = m41._sample_to_grid(lum, H, EE, NN)
        ok_ = ok_ & np.isfinite(gg)
        d_ = ok_ & dune_prior
        if int(d_.sum()) < 500:
            refused.append((name, "sees too little open dune to normalise"))
            continue
        ref = gg[d_]
        med = float(np.median(ref))
        mad = float(np.median(np.abs(ref - med)))
        if not (mad > 0):
            refused.append((name, "its open dune has no spread"))
            continue
        zz = (gg - med) / (1.4826 * mad)
        take = ok_ & (g < best)
        grid = np.where(take, zz, grid)
        best = np.where(take, g, best)
        # A SIFT-REGISTERED TILE HAS NO CONTROL-NET RESIDUAL and carries None:
        # it was not fitted to a control net at all, it was matched to the vp2
        # frame and then gated on agreeing with another capture of the same
        # ground. `agree_r` is the quantity that stands in its place, and a fit
        # with neither is reported as nan rather than crashing the read.
        rres = v.get("residual_m")
        used.append((name, g, float(rres) if rres is not None else float("nan"),
                     med, mad))
    ok = np.isfinite(grid)
    if not ok.any():
        return None, None, None, None, len(used), 0.0
    gsd = float(np.median(best[ok]))
    rr = [r for _, _, r, _, _ in used if np.isfinite(r)]
    resid = float(np.median(rr)) if rr else float("nan")
    agr = [f["agree_r"] for n_, _, _, _, _ in used
           for f in [_all_tiles().get(n_, {})] if f.get("agree_r") is not None]
    info(f"  mosaic of {len(used)} tile(s), each normalised against its own open "
         f"dune: per-cell GSD median {gsd:.3f} m (best "
         f"{float(np.min(best[ok])):.3f}), "
         + (f"agreement r median {np.median(agr):.2f}" if agr
            else f"registration residual median {resid:.2f} m"))
    info("    per-tile open dune: "
         + ", ".join(f"{m_:.0f}/{a_:.0f}" for _, _, _, m_, a_ in used)
         + "  (median/MAD — the spread between these is what compositing "
           "luminance would have added)")
    for name, why in refused:
        warn(f"    {name} left out: {why}")
    return grid, ok, gsd, resid, len(used), float(ok.sum())


def phase8(dates=None, calibrate=False, series="vp2",
           force_read=False, cut_z=None) -> int:
    """The flood read: the photographs classify, the DEM names the result.

    TWO SERIES, ONE METHOD, AND THE PRIMARY ONE IS NAMED IN ADVANCE. `series`
    chooses the imagery: "vp2" reads one committed 2.884 m/px frame per date
    through the shared vp2 homography, and "tiles" reads a mosaic of the
    2026-09-12 captures at a per-cell median near 1.0 m/px. Everything after the
    sampling step — the open-dune normalisation, the frame's own Otsu, the gate,
    the elevation-banded labelling, the scoring — is identical code, so a
    difference between the two is a difference of resolution and registration
    and not of method.

    **The tile read is primary and the vp2 read is the sensitivity check.** That
    was fixed before either was run (Martin, 2026-09-12) for the same reason
    FLOOD_OTSU_MAX_Z was fixed before the series was read: otherwise the choice
    is made on the outcome. The two are NOT independent estimates and must never
    be averaged or pooled — same imagery source, same DEM, same wells, same
    method, and at some dates quite possibly the same Google Earth imagery served
    at two zoom levels. What the pair measures is how much the 2.884 m/px read
    was costing.
    """
    from rasterio.features import geometry_mask, shapes      # noqa: PLC0415
    from rasterio.transform import from_origin                # noqa: PLC0415
    from scipy import ndimage as ndi                         # noqa: PLC0415
    from shapely.geometry import shape as shapely_shape      # noqa: PLC0415
    from PIL import Image                                    # noqa: PLC0415

    from utils.config import (CANOPY_CHANGE_GRID_M,          # noqa: PLC0415
                              CANOPY_FLOOD_MIN_PATCH_PX,
                              FLOOD_NEAR_GROUND_M, FLOOD_OTSU_MAX_Z)

    phase(8, "The flood read — the photographs classify, the DEM names")
    hol_p = OUT / "W94_06_hollows.geojson"
    if not hol_p.exists():
        warn("phase 6 has not run: W94_06_hollows.geojson is missing")
        return 1
    hollows = gpd.read_file(hol_p).set_crs(OSGB, allow_override=True)
    info(f"{len(hollows)} hollow(s) from phase 6, "
         f"{hollows.area.sum() / 1e4:.1f} ha")

    globals()["_fixed_cut"] = cut_z is not None
    tag = "" if series == "vp2" else f"_{series}"
    if cut_z is not None:
        # A FIXED CUT IS NOT A READ OF THIS FRAME and must never overwrite one.
        tag = tag + "_fixedz"
    if series == "vp2":
        man = pd.read_csv(MANIFEST, float_precision="round_trip")
        meas = man[(man["viewpoint"].astype(str).str.startswith("vp2"))
                   & (man["role"] == "measurement")].copy()
        if dates:
            meas = meas[meas["imagery_date"].isin(dates)]
        meas = meas.sort_values("imagery_date")
        if not len(meas):
            warn("no vp2 measurement frame matches; nothing to read")
            return 1
        info(f"{len(meas)} frame(s) to read: "
             f"{', '.join(meas['imagery_date'].astype(str))}")
        H, m41 = _vp2_transform()
        if H is None:
            return 1
    else:
        if not TILE_CACHE.exists():
            warn(f"no tile transform cache at {TILE_CACHE.name}; run "
                 f"'python3 tools/crossres_date_check.py --register' first")
            return 1
        import json                                          # noqa: PLC0415
        fr = json.loads(TILE_CACHE.read_text())["frames"]
        tdates = sorted({str(v["date"])[:10] for v in fr.values()
                         if v.get("series") == "tile" and v.get("date")})
        if dates:
            tdates = [d for d in tdates if d in set(dates)]
        if not tdates:
            warn("no registered tile carries a matching date; nothing to read")
            return 1
        meas = pd.DataFrame({"imagery_date": tdates, "filename": ""})
        info(f"{len(tdates)} tiled date(s) to read: {', '.join(tdates)}")
        # COVERAGE IS A PRECONDITION, not a footnote on the answer. A date below
        # a date is read and reported with its bound; it is refused only when
        # the hollow it cannot see would swallow the answer.
        # THE BOUND TRAVELS WITH THE AREA. There is no covered-fraction gate any
        # more (Martin, 2026-09-13): a gap can only hide flood where there is a
        # hollow to hold it, so every tile-derived area is reported with the
        # hollow area the tiles could not see, and a date is refused only where
        # that bound swallows the measurement.
        cov_p = REPO / "working" / "updates" / "W159_coverage_by_date.csv"
        cov = {}
        if cov_p.exists():
            c_ = pd.read_csv(cov_p, float_precision="round_trip")
            for r in c_.itertuples():
                cov[str(r.imagery_date)[:10]] = {
                    "unseen_ha": float(getattr(r, "unseen_hollow_ha", 0.0) or 0.0),
                    "unseen_frac": float(getattr(r, "unseen_hollow_frac", 0.0)
                                         or 0.0)}
            bad = [d for d in tdates
                   if cov.get(d, {}).get("unseen_frac", 0.0)
                   > HOLLOW_UNSEEN_MAX_FRAC]
            if bad:
                warn(f"  {len(bad)} date(s) cannot carry a warren-wide area — "
                     f"more than {HOLLOW_UNSEEN_MAX_FRAC * 100:.0f} % of the "
                     f"warren's hollow is unseen: "
                     + ", ".join(f"{d} ({cov[d]['unseen_ha']:.0f} ha)"
                                 for d in bad))
                tdates = [d for d in tdates if d not in set(bad)]
                meas = meas[meas["imagery_date"].isin(tdates)]
                if not len(meas):
                    return 1
        else:
            warn("  no coverage table; run tools/tile_coverage.py — an area "
                 "cannot carry its bound without it")
        m41 = _m41_module()
        H = None

    # THE FRAME'S OWN GEOMETRY, from the COMMITTED registration rather than
    # typed here: `gsd_m` converts the patch-size threshold from image pixels to
    # ground, and `residual_median_m` is how well the frame can localise a well
    # at all. Both are properties of the fit Script 41 published, so neither is
    # a number this tool is free to choose.
    gsd = resid = None
    if series == "vp2":
        rg = pd.read_csv(REPO / "outputs" / "41_canopy_cover"
                         / "41_03_registration.csv",
                         float_precision="round_trip")
        rg = rg[rg["frame"] == VP2_REFERENCE_FRAME]
        if not len(rg):
            warn(f"{VP2_REFERENCE_FRAME} is not in the committed registration")
            return 1
        gsd = float(rg["gsd_m"].iloc[0])
        resid = float(rg["residual_median_m"].iloc[0])
        info(f"vp2 registration: {gsd:.3f} m/px, median residual {resid:.2f} m "
             f"(from 41_03_registration.csv)")
    else:
        info("tile registration is PER DATE and reported with each mosaic")

    # THE GROUND GRID. Luminance is compared on the ground, never in pixel
    # space: the frames differ in viewpoint, so a pixel difference measures the
    # perspective rather than the ground.
    res = float(CANOPY_CHANGE_GRID_M)
    minx, miny, maxx, maxy = hollows.total_bounds
    minx, miny = np.floor(minx / res) * res - 200.0, np.floor(miny / res) * res - 200.0
    maxx, maxy = np.ceil(maxx / res) * res + 200.0, np.ceil(maxy / res) * res + 200.0
    ge = np.arange(minx, maxx + res, res)
    gn = np.arange(maxy, miny - res, -res)
    EE, NN = np.meshgrid(ge, gn)
    gtr = from_origin(minx - res / 2, maxy + res / 2, res, res)
    info(f"ground grid {EE.shape[1]} x {EE.shape[0]} at {res:.0f} m")

    # THE DEM ON THE SAME GRID. Used for two things only, both of which are
    # relative and so immune to the +0.22 m offset the raster carries: the 1 m
    # elevation band that splits welded water bodies, and nothing else.
    with rasterio.open(DATA_DEM) as ds:
        dem = np.array(list(ds.sample(
            np.column_stack([EE.ravel(), NN.ravel()])))).astype(float)[:, 0]
        nod = ds.nodata
    if nod is not None:
        dem[dem == nod] = np.nan
    dem = dem.reshape(EE.shape)

    hol_mask = geometry_mask(list(hollows.geometry), out_shape=EE.shape,
                             transform=gtr, invert=True)
    wells = pd.read_csv(REPO / "outputs" / "01_well_elevations.csv",
                        float_precision="round_trip")
    lev = pd.read_csv(REPO / "outputs" / "01_wells_clean.csv",
                      float_precision="round_trip")
    lev = lev.rename(columns={lev.columns[0]: "month"})
    lev["month"] = pd.to_datetime(lev["month"])

    rows, calib = [], []
    for _, fr in meas.iterrows():
        date = str(fr["imagery_date"])
        frame = str(fr["filename"])
        step(f"{date} — {frame}")
        if series == "vp2":
            fp = m41.AERIAL_DIR / frame
            if not fp.exists():
                rows.append({"date": date, "frame": frame, "verdict": "SKIPPED",
                             "reason": "frame not on disk"})
                warn("  frame not on disk")
                _clear_date(date, tag)
                continue
            a = np.asarray(Image.open(fp).convert("RGB")).astype(float)
            lum = (0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1]
                   + 0.0722 * a[:, :, 2])
            grid, ok = m41._sample_to_grid(lum, H, EE, NN)
        else:
            # The date's own warren mask is needed BEFORE sampling here, because
            # each tile normalises against the open dune it can see.
            wm0 = geometry_mask([warren_on(date)], out_shape=EE.shape,
                                transform=gtr, invert=True)
            grid, ok, gsd, resid, n_used, _ = _mosaic(
                date, m41, EE, NN, wm0 & ~hol_mask & np.isfinite(dem))
            frame = f"{n_used} tile(s)"
            if grid is None:
                rows.append({"date": date, "frame": frame, "verdict": "SKIPPED",
                             "reason": "no tile of this date is on disk or "
                                       "registered"})
                warn("  no usable tile for this date")
                _clear_date(date, tag)
                continue

        # THE MASK IS DATE-DEPENDENT. `warren_on` subtracts the canopy as at
        # this date, so a block that had closed by now is not read as ground.
        wmask = geometry_mask([warren_on(date)], out_shape=EE.shape,
                              transform=gtr, invert=True)
        usable = wmask & ok & np.isfinite(grid) & np.isfinite(dem)

        # BUSHES ARE EXCLUDED FROM THE ANALYSIS, not subtracted from its result
        # (Martin, 2026-09-14: "mark these as bushes and exclude from the
        # analysis"). A cell under scrub cannot be classified as water on ANY
        # frame, so the correction cannot be forgotten by a later reader, cannot
        # be applied twice, and never enters the open-dune reference either.
        # The cost is stated rather than hidden: a slack that genuinely floods
        # UNDER a bush is unreadable there, so every area is a lower bound by
        # whatever of the mask falls inside a hollow.
        #
        # NOT APPLIED UNDER --cut-z, because the fixed-cut read of a dry frame is
        # what BUILDS the mask (phase 19) and masking its own source would erase
        # the measurement.
        bmask = None
        if cut_z is None:
            bm = _bush_mask_geom()
            if bm is not None:
                before = int(usable.sum())
                bmask = geometry_mask([bm], out_shape=EE.shape, transform=gtr,
                                      invert=True)
                usable = usable & ~bmask
                info(f"  bush mask: {before - int(usable.sum())} cell(s) held "
                     f"out of the classification and out of the open-dune "
                     f"reference; those inside a hollow that reads wet are "
                     f"restored below")
        if usable.sum() < 1000:
            rows.append({"date": date, "frame": frame, "verdict": "SKIPPED",
                         "reason": "the warren is barely in this frame's window"})
            warn("  the warren is barely inside this frame's usable window")
            continue

        # NORMALISE AGAINST THIS FRAME'S OWN OPEN DUNE — the warren less the
        # mapped hollows, which by construction never floods. Robust, because a
        # few genuinely dark cells in it must not move the reference.
        dune = usable & ~hol_mask
        ref = grid[dune]
        med = float(np.median(ref))
        mad = float(np.median(np.abs(ref - med)))
        sigma = 1.4826 * mad if mad > 0 else float("nan")
        if not np.isfinite(sigma) or sigma <= 0:
            rows.append({"date": date, "frame": frame, "verdict": "SKIPPED",
                         "reason": "the open-dune reference has no spread"})
            warn("  the open-dune reference has no spread")
            continue
        z = (grid - med) / sigma
        info(f"  open dune: median {med:.1f}, MAD {mad:.1f} over "
             f"{int(dune.sum())} cell(s); {int(usable.sum())} usable")

        # THE CUT IS THIS FRAME'S OWN OTSU THRESHOLD, and the GATE is where that
        # threshold falls. A dry frame fails here on its own evidence rather
        # than being argued away afterwards: Otsu always returns a threshold,
        # but on a dry frame it splits bright from brighter, at or above the
        # dune median, because there is no dark population to find.
        thr, frac = _otsu(z[usable])
        info(f"  Otsu on z: threshold {thr:.2f} (gate {FLOOD_OTSU_MAX_Z}), "
             f"between-class variance {frac:.3f} of total (diagnostic only)")

        if calibrate:
            wl = _well_levels(lev, wells, date)
            for _, wr in wl.iterrows():
                c, r0 = ~gtr * (wr["E"], wr["N"])
                c, r0 = int(c), int(r0)
                if 0 <= r0 < z.shape[0] and 0 <= c < z.shape[1] and usable[r0, c]:
                    calib.append({"date": date, "well": wr["well"],
                                  "h_m": wr["h_m"], "wet_truth": wr["h_m"] >= 0,
                                  "lum": float(grid[r0, c]),
                                  "z": float(z[r0, c]),
                                  "otsu_z": thr, "bimodal_frac": frac})
            continue

        if cut_z is not None:
            # THE CUT COMES FROM ANOTHER FRAME, AND THAT IS THE POINT (D-167).
            # z is standardised against each frame's OWN open dune - median and
            # 1.4826*MAD - so a threshold in z is comparable between frames in a
            # way a luminance is not. Applying an ACCEPTED wet frame's cut to a
            # frame with no water asks the only question a dry frame can answer:
            # what is still darker than water-dark when there is no water? That
            # is a bush, a shadow, a dark ditch - a FALSE WET FEATURE, which is
            # what Martin gave these frames for (2026-09-14).
            #
            # Letting the dry frame choose its own Otsu instead is what produced
            # 87.86 ha on 2009-04-20 and 288.44 ha here on 2019-09-11, because
            # Otsu always returns a threshold and on a dry frame it splits
            # bright from brighter: 2019-09-11's own split sits at z = +1.79,
            # ABOVE its dune median, so everything but a sunlit crest came out
            # as water. The gate exists to refuse exactly that, and --force-read
            # overrode the one measurement that was working.
            step(f"  FIXED CUT z = {cut_z:.3f} applied in place of this frame's "
                 f"own split ({thr:.2f}); the gate does not apply because the "
                 f"threshold is not this frame's to choose")
            thr = float(cut_z)
        elif force_read and np.isfinite(thr) and thr > FLOOD_OTSU_MAX_Z:
            # THE GATE IS OVERRIDDEN FOR THIS FRAME, ON MARTIN'S JUDGEMENT OF
            # THE IMAGE (2026-09-13, for 2017-03-24). The gate is not wrong in
            # general: on a frame with no dark population Otsu splits bright
            # from brighter and the cut is arbitrary. But it is a test of
            # DARKNESS, and water that is specular - brighter than its rim and
            # colourless - defeats it, which is a known failure here. A read
            # produced this way is flagged `forced` in every row it writes so it
            # can never be mistaken for one the frame's own evidence supported.
            warn(f"  GATE OVERRIDDEN: split at {thr:.2f} is above "
                 f"{FLOOD_OTSU_MAX_Z}; reading anyway on instruction, and the "
                 f"row is flagged forced")
        elif not np.isfinite(thr) or thr > FLOOD_OTSU_MAX_Z:
            rows.append({"date": date, "frame": frame, "n_bodies": 0,
                         "flood_ha": 0.0, "otsu_z": round(float(thr), 4),
                         "bimodal_frac": round(frac, 4), "verdict": "DRY",
                         "reason": f"the frame's own split falls at "
                                   f"{thr:.2f}, above {FLOOD_OTSU_MAX_Z} — no "
                                   f"dark population"})
            step("  DRY — the frame's own split is not on the dark side of its "
                 "own dune; no cut applied")
            _clear_date(date, tag)
            continue

        wet = usable & (z <= thr)

        # A TREE IN A WET HOLLOW IS STANDING IN WATER (Martin, 2026-09-14:
        # "in wet frames where the trees sit in hollows you count as wet").
        # The canopy hides the ground; it does not drain it. So the mask is not
        # a blanket exclusion - it says only that a bush cell carries NO
        # EVIDENCE of its own, and the evidence is then taken from the hollow
        # around it.
        #
        # THE DRY CASE FALLS OUT WITH NO SPECIAL RULE: a dry frame classifies no
        # water, so no hollow qualifies, so nothing is restored and the bushes
        # read as no water. That is the whole point of the two-sided rule.
        #
        # TWO CONDITIONS, because neither alone is defensible. The bush must lie
        # in a hollow that holds classified water SOMEWHERE ELSE - a bush in a
        # dry hollow stays dry - and it must sit AT OR BELOW the highest water
        # cell in that hollow, because water is level (D-159). A bush on the rim
        # of a flooded slack is not in the water.
        if bmask is not None and wet.any():
            from rasterio.features import rasterize            # noqa: PLC0415
            hid = rasterize(
                [(g, int(s)) for g, s in zip(hollows.geometry, hollows["slack"])
                 if pd.notna(s)],
                out_shape=EE.shape, transform=gtr, fill=0, dtype="int32")
            add = np.zeros_like(wet)
            for h in np.unique(hid[wet & (hid > 0)]):
                inh = hid == h
                lvl = np.nanmax(np.where(wet & inh, dem, np.nan))
                if not np.isfinite(lvl):
                    continue
                add |= inh & bmask & ~wet & np.isfinite(dem) & (dem <= lvl)
            if add.any():
                wet = wet | add
                info(f"  {int(add.sum())} bush cell(s) restored as wet "
                     f"({add.sum() * res * res / 1e4:.2f} ha): in a hollow that "
                     f"reads wet, at or below its water level")

        # A WATER BODY IS LEVEL, and that is a filter. Labelling flood cells in
        # plan alone welded 45.7 ha across 13.4 m of relief — slacks joined by
        # dark threads over the ridges between them. Labelling within 1 m
        # elevation bands splits them without cutting genuine water in half,
        # which tighter bands do (D-159).
        band = np.floor(np.where(np.isfinite(dem), dem, 0.0)).astype(int)
        lab = np.zeros(wet.shape, dtype=np.int32)
        nxt = 0
        for b in np.unique(band[wet]):
            m_ = wet & (band == b)
            ll, nn_ = ndi.label(m_)
            ll[ll > 0] += nxt
            lab = np.where(m_, ll, lab)
            nxt += nn_
        if nxt:
            # CANOPY_FLOOD_MIN_PATCH_PX IS IN IMAGE PIXELS at the frame's own
            # GSD — that is how config.py derives it — and the labelling here is
            # on the 2 m GROUND grid. Comparing the two directly applied a
            # threshold two-fifths of the documented size.
            min_cells = int(round(CANOPY_FLOOD_MIN_PATCH_PX * gsd * gsd
                                  / (res * res)))
            counts = np.bincount(lab.ravel())
            small = np.flatnonzero(counts < min_cells)
            drop = np.zeros(counts.size, bool)
            drop[small] = True
            drop[0] = True
            lab = np.where(drop[lab], 0, lab)
        n_bodies = int(len(np.unique(lab)) - 1)
        polys, ids = [], []
        for geom, val in shapes(lab, mask=(lab > 0), transform=gtr):
            polys.append(shapely_shape(geom))
            ids.append(int(val))
        if not polys:
            rows.append({"date": date, "frame": frame, "n_bodies": 0,
                         "flood_ha": 0.0, "otsu_z": round(float(thr), 4),
                         "bimodal_frac": round(frac, 4),
                         "verdict": "READ", "reason": "no body survived the "
                                                      "minimum patch size"})
            step("  no body survived the minimum patch size")
            _clear_date(date, tag)
            continue
        fg = gpd.GeoDataFrame({"body_id": ids}, geometry=polys, crs=OSGB)
        fg = fg.dissolve(by="body_id", as_index=False)
        fg["area_m2"] = fg.area.round(1)
        fg["elev_band_m"] = [int(np.floor(np.nanmedian(dem[lab == i])))
                             for i in fg["body_id"]]
        fg["median_z"] = [round(float(np.nanmedian(z[lab == i])), 3)
                          for i in fg["body_id"]]
        # ATTRIBUTION, not delineation: the hollow NAMES the body. The DEM does
        # not decide where water is allowed to be (D-159's inversion).
        j = gpd.sjoin(fg[["body_id", "geometry"]], hollows[["slack", "geometry"]],
                      how="left", predicate="intersects")
        j = j.drop_duplicates("body_id")[["body_id", "slack"]]
        fg = fg.merge(j, on="body_id", how="left")
        fg["slack"] = fg["slack"].astype("Int64")

        sc = _score(fg, lev, wells, date, gtr, usable, FLOOD_NEAR_GROUND_M,
                    resid)
        _flood_map(date, frame, fg, hollows, sc, thr, tag)
        if len(sc["per_well"]):
            p = OUT / f"W94_08_wells{tag}_{date}.csv"
            sc["per_well"].to_csv(p, index=False)
            saved(p.name)
        else:
            # NO FILE RATHER THAN AN EMPTY ONE. A zero-row frame wrote a
            # headerless CSV that every later reader choked on; 2026-03-31 has
            # no dipwell month at all, the record ending at
            # REFERENCE_CUTOFF_DATE, and that is a fact to state, not a file.
            warn(f"  no dipwell month for {date}: the read cannot be scored")
        for stem, gdf in ((f"W94_08_flood{tag}_{date}", fg),):
            q = OUT / f"{stem}.geojson"
            q.write_text(gdf.to_json(), encoding="utf-8")
            saved(q.name)
            tmp = Path(tempfile.mkdtemp()) / "flood.kml"
            gdf.to_crs("EPSG:4326").to_file(tmp, driver="KML")
            q = OUT / f"{stem}.kml"
            q.write_bytes(tmp.read_bytes())
            shutil.rmtree(tmp.parent, ignore_errors=True)
            saved(q.name)
        row = {"date": date, "frame": frame,
               "transform_source": ("vp2 (shared)" if series == "vp2"
                                    else f"tiles (per frame, {gsd:.3f} m/px)"),
               "gsd_m": round(float(gsd), 3),
               "registration_residual_m": (round(float(resid), 2)
                                           if resid is not None
                                           and np.isfinite(resid) else None),
               "unseen_hollow_ha": (round(cov.get(date, {}).get("unseen_ha", 0.0), 2)
                                    if series == "tiles" else None),
               "n_bodies": n_bodies, "flood_ha": round(fg.area.sum() / 1e4, 3),
               "otsu_z": round(float(thr), 4), "forced": bool(force_read),
               "cut_z_fixed": (None if cut_z is None else round(float(cut_z), 4)),
               "bimodal_frac": round(frac, 4), "verdict": "READ", "reason": ""}
        row.update(sc["summary"])
        rows.append(row)
        if series == "tiles" and cov.get(date):
            info(f"  bound: at most {cov[date]['unseen_ha']:.2f} ha of hollow is "
                 f"outside every tile, so this area is a floor by that much")
        step(f"  {n_bodies} body(ies), {fg.area.sum() / 1e4:.2f} ha; "
             f"recall {sc['summary']['recall']}, "
             f"precision {sc['summary']['precision']}, "
             f"agreement {sc['summary']['agreement']} at "
             f"{sc['summary']['n_wells']} wells")

    if calibrate:
        if not calib:
            warn("no calibration rows — no well fell in a usable cell")
            return 1
        cdf = pd.DataFrame(calib)
        # MERGE BY DATE, never overwrite. Calibration is built up one frame at a
        # time — the wet frame sets the cut, the record's dry frames set the
        # gate — and a run that replaced the file lost the frame before it.
        p = OUT / f"W94_08_calibration{tag}.csv"
        if p.exists():
            prev = pd.read_csv(p, float_precision="round_trip")
            prev = prev[~prev["date"].isin(cdf["date"].unique())]
            cdf = pd.concat([prev, cdf], ignore_index=True)
        cdf = cdf.sort_values(["date", "well"])
        cdf.to_csv(p, index=False)
        saved(p.name)
        for d, g in cdf.groupby("date"):
            wet_, dry_ = g[g.wet_truth], g[~g.wet_truth]
            info(f"  {d}: {len(wet_)} wet / {len(dry_)} dry wells; "
                 f"z median wet "
                 f"{(wet_['z'].median() if len(wet_) else float('nan')):.2f}, "
                 f"dry {(dry_['z'].median() if len(dry_) else float('nan')):.2f}; "
                 f"bimodal {g['bimodal_frac'].iloc[0]:.3f}")
        info("FREEZE FLOOD_LUM_Z between the two medians and FLOOD_BIMODAL_MIN "
             "below the calibration frame's fraction, in config.py, then run "
             "without --calibrate.")
        return 0

    sdf = pd.DataFrame(rows)
    # ONE FILE PER SERIES, and the file is MERGED BY DATE rather than replaced.
    # A partial-date run used to overwrite the whole table and lose every date it
    # did not read — the defect the 2026-09-12 review named in W94_09_scores.csv,
    # fixed here for both series at once.
    p = OUT / f"W94_09_scores{tag}.csv"
    if p.exists() and len(sdf):
        prev = pd.read_csv(p, float_precision="round_trip")
        prev = prev[~prev["date"].astype(str).isin(sdf["date"].astype(str))]
        sdf = pd.concat([prev, sdf], ignore_index=True)
    sdf = sdf.sort_values("date")
    sdf.to_csv(p, index=False)
    saved(p.name)
    return 0


def _stale_cells(date, m41, EE, NN, dune_prior):
    """Cells whose imagery is IDENTICAL to an earlier date's — served stale.

    Martin, 2026-09-09, on 2020-03-31: "there is a small area to the east which
    is stale imagery from sept 19 which is dry, you can tell by the vertical
    break in the colour." The break is real and already measured — 11.2 % of the
    warren is identical between 2019-09-11 and 2020-03-31 — and it is found HERE
    BY IDENTITY rather than by looking for a straight line or a colour step.

    That choice matters. A seam detector would need a threshold on colour and an
    assumption that the seam is straight, and it would be drawn on the date whose
    answer we are about to question. Identity needs neither: a stale block is not
    merely similar to the earlier imagery, it IS the earlier imagery, pixel for
    pixel, and the same test that found the 2010-05-27 / 2011-06-19 duplicate
    finds it at cell level. It also generalises — every date is checked against
    every earlier one, which is the per-frame stale-patch check GEO_PROVENANCE
    has had as owed since 2026-09-11.

    Returns (mask, report). Cells in the mask are excluded from the date's read,
    because imagery from another date cannot evidence water on this one.
    """
    from PIL import Image                                    # noqa: PLC0415
    from scipy import ndimage as ndi                         # noqa: PLC0415

    mine = _tile_frames(date)
    if not mine:
        return np.zeros(EE.shape, bool), []
    earlier = sorted({str(v["date"])[:10] for _, v in
                      [(k, v) for k, v in _all_tiles().items()]
                      if v.get("date") and str(v["date"])[:10] < date})
    if not earlier:
        return np.zeros(EE.shape, bool), []

    def _grid_of(tiles):
        g = np.full(EE.shape, np.nan)
        best = np.full(EE.shape, np.inf)
        for name, v in tiles:
            fp = TILE_DIR / name
            if not fp.exists():
                continue
            gs = float(v["gsd_m"])
            a = np.asarray(Image.open(fp).convert("RGB")).astype(float)
            lum = (0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1]
                   + 0.0722 * a[:, :, 2])
            H = m41._homography(np.asarray(v["pairs"], float))
            gg, ok_ = m41._sample_to_grid(lum, H, EE, NN)
            take = ok_ & np.isfinite(gg) & (gs < best)
            g = np.where(take, gg, g)
            best = np.where(take, gs, best)
        return g

    mineg = _grid_of(mine)
    stale = np.zeros(EE.shape, bool)
    report = []
    for d0 in earlier:
        other = _tile_frames(d0)
        if not other:
            continue
        og = _grid_of(other)
        same = (np.abs(mineg - og) <= STALE_IDENTICAL_TOL) & dune_prior
        if not same.any():
            continue
        # ONE CELL MATCHING BY CHANCE IS NOT A STALE BLOCK. Two smooth sand
        # surfaces agree here and there at any tolerance; a served block is
        # CONTIGUOUS and large. Only components above the smallest thing this
        # project calls a slack are taken, for the same reason phase 9 uses that
        # radius: below it, nothing that matters can hide.
        lab, n = ndi.label(same)
        if not n:
            continue
        cell_m2 = float(abs(EE[0, 1] - EE[0, 0])) ** 2
        keep = np.zeros(n + 1, bool)
        counts = np.bincount(lab.ravel(), minlength=n + 1)
        keep[1:] = counts[1:] * cell_m2 >= STALE_MIN_BLOCK_M2
        block = keep[lab]
        if not block.any():
            continue
        stale |= block
        report.append({"source_date": d0,
                       "area_ha": round(float(block.sum()) * cell_m2 / 1e4, 2),
                       "n_blocks": int(keep.sum())})
        warn(f"    STALE: {report[-1]['area_ha']:.2f} ha identical to {d0} "
             f"in {report[-1]['n_blocks']} block(s) — excluded, because imagery "
             f"from {d0} cannot evidence water on {date}")
    return stale, report


def _all_tiles():
    import json                                              # noqa: PLC0415
    if not TILE_CACHE.exists():
        return {}
    return {k: v for k, v in json.loads(TILE_CACHE.read_text())["frames"].items()
            if v.get("series") == "tile"}


def phase10(dates=None, calibrate=False) -> int:
    """The slack-edge classifier: each slack judged against its OWN rim.

    WHY THE OPEN-DUNE REFERENCE HAD TO GO. Phase 8 normalises a whole frame
    against the warren's open dune and cuts at the frame's own Otsu threshold.
    That works at the vp2 viewpoint's 2.884 m/px and it does not survive the
    2026-09-12 captures, measured 2026-09-12: the open-dune MAD is 7-32 at tile
    resolution against 8.9-14.2 at vp2, it differs between tiles of ONE date, and
    the per-tile Otsu thresholds of a wet date (-0.46 to +0.48 on 2021-04-04)
    overlap those of a dry one (-1.63 to +1.60 on 2012-05-26). No threshold
    separates overlapping bands. Finer imagery resolves the dune texture that
    2.884 m/px averaged away, so the reference itself became noisy.

    SO THE REFERENCE IS LOCAL: a slack's floor against its own rim, metres away,
    in the SAME tile. Exposure, sun angle, view geometry and dune texture scale
    are then common to both sides of the comparison and cancel by construction,
    which is what no global reference could do.

    AND THE TEST IS TWO-SIDED, because Martin saw why it had to be (2026-09-12):
    on 2021-04-04 the sun and clouds reflect off the pools and turn the water
    WHITE. A detector looking for dark water does not merely miss that water, it
    scores it as drier than sand — which is the sign error behind 2020-03-31's
    wet wells sitting at z +0.85 against +0.13 for its dry ones. Water differs
    from its rim; whether it differs downward or upward is a fact about the sky.

    Three contrasts per slack per tile, each in units of the RIM's own robust
    spread so they are comparable between slacks and dates:

      dL    luminance, floor minus rim. Negative is dark water.
      dBR   blue minus red, floor minus rim. Positive is water: water absorbs
            red and reflects sky, so it goes blue whether it is dark or glaring.
      dS    saturation, floor minus rim. Specular reflection of a bright sky is
            near-neutral, so glare goes NEGATIVE here while bright dry sand, which
            is warm-toned, does not.

    THE THREE ARE COMBINED, NOT THRESHOLDED ONE AT A TIME, and one signed score
    carries them: SCORE = -dL + dBR + dS, oriented so water is positive. Measured
    on 2021-03-24 against the dipwell record (32 wet-well slacks, 10 dry-well),
    every channel separates in the direction physics predicts —

        dL  -0.64 wet against +0.03 dry     water is darker than its rim
        dBR +0.67 against  0.00            water is bluer: it absorbs red
        dS  +0.38 against -0.15            water is more SATURATED: it is
                                           coloured where sand is pale

    — and every one of those wet medians still sits inside the dry controls' own
    1-99 percentile range on its own channel. Three weak separators sum to one
    that separates; a single-channel cut set from the dry dates cannot help being
    conservative.

    THE GLARE BRANCH IS GONE, and its removal is a correction. v1.8.0 tested for
    brighter-and-DESATURATED, on the reasoning that specular sky is near-neutral.
    The measurement says the opposite for water in general — wet slacks are MORE
    saturated than their rims — so that branch was voting against the signal it
    was meant to add. Glare of the kind Martin saw on 2021-04-04 applies to that
    one date (Martin, 2026-09-13) and is a documented exception to be handled by
    inspection, not a general branch that costs every other date accuracy.

    THE DEM NEVER PROMOTES A SLACK. It supplies the geometry — which cells are
    floor and which are rim — and nothing else; a slack with no contrast is DRY,
    not unknown. That keeps D-159's direction intact ("the photographs classify,
    the DEM names the result") and keeps the read falsifiable, which a
    DEM-decides classifier could not be: it would call every slack wet on every
    date, including the dry ones.

    WHICH IS THE TEST. `--calibrate` reports the contrast distributions on the
    DRY dates only, and the thresholds are to be set so those dates return
    essentially no wet slacks. The wet dates are then read with thresholds that
    never saw them. Same discipline that made FLOOD_OTSU_MAX_Z worth having.
    """
    from PIL import Image                                    # noqa: PLC0415
    from rasterio.features import geometry_mask              # noqa: PLC0415
    from rasterio.transform import from_origin               # noqa: PLC0415

    from utils.config import (CANOPY_CHANGE_GRID_M,          # noqa: PLC0415
                              SLACK_MIN_AREA_M2)
    phase(10, "The slack-edge classifier — each slack against its own rim")

    hol_p = OUT / "W94_06_hollows.geojson"
    if not hol_p.exists():
        warn("phase 6 has not run: W94_06_hollows.geojson is missing")
        return 1
    hollows = gpd.read_file(hol_p).set_crs(OSGB, allow_override=True)
    if not TILE_CACHE.exists():
        warn(f"no tile transform cache at {TILE_CACHE.name}; run "
             f"'python3 tools/crossres_date_check.py --register' first")
        return 1
    m41 = _m41_module()
    tdates = sorted({str(v["date"])[:10] for v in _all_tiles().values()
                     if v.get("date")})
    if dates:
        tdates = [d for d in tdates if d in set(dates)]
    if not tdates:
        warn("no registered tile carries a matching date")
        return 1
    info(f"{len(hollows)} hollow(s); {len(tdates)} date(s): {', '.join(tdates)}")

    res = float(CANOPY_CHANGE_GRID_M)
    minx, miny, maxx, maxy = hollows.total_bounds
    minx, miny = np.floor(minx / res) * res - 200.0, np.floor(miny / res) * res - 200.0
    maxx, maxy = np.ceil(maxx / res) * res + 200.0, np.ceil(maxy / res) * res + 200.0
    ge = np.arange(minx, maxx + res, res)
    gn = np.arange(maxy, miny - res, -res)
    EE, NN = np.meshgrid(ge, gn)
    gtr = from_origin(minx - res / 2, maxy + res / 2, res, res)
    hol_mask = geometry_mask(list(hollows.geometry), out_shape=EE.shape,
                            transform=gtr, invert=True)

    # THE RIM RADIUS IS DERIVED, NOT CHOSEN — the same quantity phase 9 uses:
    # sqrt(SLACK_MIN_AREA_M2 / pi) is the radius of the smallest thing this
    # project calls a slack, so a ring that wide is the nearest ground that is
    # certainly not this slack's floor.
    rim_r = float(np.sqrt(SLACK_MIN_AREA_M2 / np.pi))
    info(f"rim ring = sqrt(SLACK_MIN_AREA_M2 / pi) = {rim_r:.2f} m — derived")

    # FLOORS AND RIMS AS TWO LABEL RASTERS, in two passes over the grid rather
    # than two per slack. Rasterising each of 1078 hollows separately means 2156
    # full-grid rasterisations and does not finish; labelling once and assigning
    # every background cell to its NEAREST slack by an exact Euclidean transform
    # gives the same answer in two passes. It also settles, rather than leaves
    # arbitrary, what happens where two slacks are within a rim's width of each
    # other: the cell belongs to the nearer one, and to neither if it is inside
    # any hollow.
    from rasterio.features import rasterize                  # noqa: PLC0415
    from scipy import ndimage as ndi2                        # noqa: PLC0415
    step("labelling each slack's floor, and its own rim by nearest slack")
    shp = [(g, int(sid)) for g, sid in zip(hollows.geometry, hollows["slack"])
           if pd.notna(sid)]
    if not shp:
        warn("the hollows carry no slack id; nothing to classify")
        return 1
    lab = rasterize(shp, out_shape=EE.shape, transform=gtr, fill=0,
                    dtype="int32", all_touched=False)
    bg = lab == 0
    dist, idx = ndi2.distance_transform_edt(bg, sampling=(res, res),
                                            return_indices=True)
    near = lab[idx[0], idx[1]]
    rim_all = bg & (dist <= rim_r) & ~hol_mask
    rlab = np.where(rim_all, near, 0).astype("int32")
    nf = np.bincount(lab.ravel())
    nr = np.bincount(rlab.ravel())
    sids = np.array(sorted({sid for _, sid in shp}), dtype="int64")
    ok_sid = np.array([(nf[s] if s < len(nf) else 0) >= MIN_SLACK_CELLS
                       and (nr[s] if s < len(nr) else 0) >= MIN_SLACK_CELLS
                       for s in sids])
    sids = sids[ok_sid]
    info(f"{len(sids)} slack(s) of {len(shp)} have both a floor and a rim of at "
         f"least {MIN_SLACK_CELLS} cell(s) at {res:.0f} m")
    if not len(sids):
        warn("no slack has a usable floor and rim; nothing to classify")
        return 1

    rows = []
    for date in tdates:
        step(f"{date}")
        wm = geometry_mask([warren_on(date)], out_shape=EE.shape,
                           transform=gtr, invert=True)
        stale, _rep = _stale_cells(date, m41, EE, NN, wm & ~hol_mask)
        live = wm & ~stale
        tiles = _tile_frames(date)
        if not tiles:
            warn("  no registered tile for this date")
            continue
        # EVERY CONTRAST IS COMPUTED INSIDE ONE TILE. Crossing tiles would put
        # the exposure and the view geometry back into the comparison, which is
        # the whole thing this phase exists to remove.
        per_slack = {}
        for name, v in tiles:
            fp = TILE_DIR / name
            if not fp.exists():
                continue
            gsd = float(v["gsd_m"])
            a = np.asarray(Image.open(fp).convert("RGB")).astype(float)
            L = 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]
            BR = a[:, :, 2] - a[:, :, 0]
            mx = a.max(axis=2)
            S = np.where(mx > 0, (mx - a.min(axis=2)) / np.maximum(mx, 1.0), 0.0)
            H = m41._homography(np.asarray(v["pairs"], float))
            gL, ok_ = m41._sample_to_grid(L, H, EE, NN)
            gB, _ = m41._sample_to_grid(BR, H, EE, NN)
            gS, _ = m41._sample_to_grid(S * 100.0, H, EE, NN)
            ok_ = ok_ & np.isfinite(gL) & live
            # EVERY SLACK AT ONCE, through labelled reductions. Looping 1078
            # slacks x 3 channels x 6 tiles in Python does not finish; the same
            # medians and MADs come out of ndimage's labelled reductions in a
            # handful of passes.
            fl = np.where(ok_, lab, 0)
            rl = np.where(ok_, rlab, 0)
            cf = np.bincount(fl.ravel(), minlength=int(sids.max()) + 1)
            cr = np.bincount(rl.ravel(), minlength=int(sids.max()) + 1)
            live_sid = sids[(cf[sids] >= MIN_SLACK_CELLS)
                            & (cr[sids] >= MIN_SLACK_CELLS)]
            if not len(live_sid):
                continue
            stat = {}
            for key, arr in (("dL", gL), ("dBR", gB), ("dS", gS)):
                a_ = np.where(np.isfinite(arr), arr, 0.0)
                rmed = np.asarray(ndi2.median(a_, rl, index=live_sid), float)
                look = np.zeros(int(sids.max()) + 1)
                look[live_sid] = rmed
                rdev = np.abs(a_ - look[rl])
                rmad = np.asarray(ndi2.median(rdev, rl, index=live_sid), float)
                fmed = np.asarray(ndi2.median(a_, fl, index=live_sid), float)
                sd = 1.4826 * rmad
                with np.errstate(invalid="ignore", divide="ignore"):
                    stat[key] = np.where(sd > 0, (fmed - rmed) / sd, np.nan)
            for k, sid in enumerate(live_sid):
                sid = int(sid)
                out = {"date": date, "slack": sid, "tile": name, "gsd_m": gsd,
                       "n_floor": int(cf[sid]), "n_rim": int(cr[sid])}
                for key in ("dL", "dBR", "dS"):
                    v = float(stat[key][k])
                    out[key] = round(v, 3) if np.isfinite(v) else None
                prev = per_slack.get(sid)
                # FINEST TILE WINS, as in the mosaic — but the statistic was
                # computed wholly inside that tile, so nothing is mixed.
                if prev is None or gsd < prev["gsd_m"]:
                    per_slack[sid] = out
        rows.extend(per_slack.values())
        info(f"  {len(per_slack)} slack(s) measured in at least one tile")

    if not rows:
        warn("no slack could be measured on any date")
        return 1
    D = pd.DataFrame(rows)
    # MERGED BY DATE, never replaced — the same defect W94_09_scores had. A run
    # over two dates must not delete the other fourteen.
    p = OUT / "W94_20_slack_contrast.csv"
    if p.exists():
        prev = pd.read_csv(p, float_precision="round_trip")
        prev = prev[~prev["date"].astype(str).isin(D["date"].astype(str))]
        D = pd.concat([prev, D], ignore_index=True)
    D = D.sort_values(["date", "slack"])
    D.to_csv(p, index=False)
    saved(p.name)

    if calibrate:
        step("contrast on the DRY dates — the thresholds come from here, and "
             "from here only")
        dry = D[D["date"].isin(DRY_CALIBRATION_DATES)]
        if not len(dry):
            warn("none of the dry calibration dates is in this run; pass them "
                 "with --date")
            return 1
        dry = dry.assign(score=(-dry["dL"].fillna(0) + dry["dBR"].fillna(0)
                                + dry["dS"].fillna(0)))
        for key, tail in (("dL", "low"), ("dBR", "high"), ("dS", "high"),
                          ("score", "high")):
            v = dry[key].dropna()
            if not len(v):
                continue
            q = np.percentile(v, [0.5, 1, 50, 99, 99.5])
            info(f"  {key:5s}: n {len(v)}  median {q[2]:+.2f}  "
                 f"p1 {q[1]:+.2f}  p99 {q[3]:+.2f}  "
                 f"p0.5 {q[0]:+.2f}  p99.5 {q[4]:+.2f}   ({tail} tail is water)")
        v = dry["score"].dropna()
        if len(v):
            info(f"  SLACK_WET_SCORE_MIN at the dry controls' p99 is "
                 f"{np.percentile(v, 99):+.2f} and at p99.5 "
                 f"{np.percentile(v, 99.5):+.2f}. A threshold there admits that "
                 f"fraction of DRY slacks by construction — 1 in 100 or 1 in 200 "
                 f"— which is the false-positive rate you are choosing, stated "
                 f"before any wet date is read.")
        return 0

    try:
        from utils.config import SLACK_WET_SCORE_MIN          # noqa: PLC0415
    except ImportError:
        warn("SLACK_WET_SCORE_MIN is not in config.py yet; run --calibrate and "
             "set it from the dry dates' own upper tail")
        return 1

    D["score"] = (-D["dL"].fillna(0) + D["dBR"].fillna(0) + D["dS"].fillna(0))
    D.loc[D[["dL", "dBR", "dS"]].isna().all(axis=1), "score"] = np.nan
    D["wet"] = D["score"].notna() & (D["score"] >= SLACK_WET_SCORE_MIN)
    D.to_csv(p, index=False)
    saved(p.name)
    step("wet slacks by date:")
    for d, g in D.groupby("date"):
        lab = "DRY CONTROL" if d in DRY_CALIBRATION_DATES else "           "
        info(f"  {d} {lab}  {int(g['wet'].sum()):4d} of {len(g):4d} slack(s) wet"
             f"   score median {g['score'].median():+.2f}, "
             f"p95 {g['score'].quantile(0.95):+.2f}")
    ctrl = D[D["date"].isin(DRY_CALIBRATION_DATES)]
    if len(ctrl):
        f = float(ctrl["wet"].mean())
        step(f"THE FALSIFICATION TEST: {f * 100:.2f} % of slack-dates wet on the "
             f"dry controls ({int(ctrl['wet'].sum())} of {len(ctrl)})")
        if f > 0.05:
            warn("  THE CONTROLS FAIL. More than 5 % of slacks read wet on dates "
                 "with no water, so these thresholds are detecting substrate or "
                 "vegetation and the read is not usable. Do not quote a wet-date "
                 "number from this run.")
    info("NO AREA AND NO POLYGON IS WRITTEN BY THIS PHASE. It classifies slacks, "
         "which is a different claim from delineating a waterline, and the two "
         "must not be conflated in a document.")
    return 0


def _date_surface(date, m41, EE, NN, dune_prior):
    """One date's tiles as three normalised, mosaicked surfaces.

    Returns (L, BR, S, ok, gsd) where each surface is in units of that TILE's own
    open-dune spread — normalised per tile before compositing, because every
    Google Earth capture carries its own exposure and a composite of raw
    luminance has variance BETWEEN tiles on top of the variance within each
    (measured 2026-09-12: open-dune MAD 26.9 composited against 7-32 per tile).
    """
    from PIL import Image                                    # noqa: PLC0415
    tiles = _tile_frames(date)
    if not tiles:
        return None, None, None, None, None
    outs = {k: np.full(EE.shape, np.nan) for k in ("L", "BR", "S")}
    best = np.full(EE.shape, np.inf)
    used = 0
    for name, v in tiles:
        fp = TILE_DIR / name
        if not fp.exists():
            continue
        g = float(v["gsd_m"])
        a = np.asarray(Image.open(fp).convert("RGB")).astype(float)
        mx = a.max(axis=2)
        chans = {
            "L": 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2],
            "BR": a[:, :, 2] - a[:, :, 0],
            "S": np.where(mx > 0, (mx - a.min(axis=2)) / np.maximum(mx, 1.0),
                          0.0) * 100.0,
        }
        H = m41._homography(np.asarray(v["pairs"], float))
        samp, ok0 = {}, None
        for k, arr in chans.items():
            gg, ok_ = m41._sample_to_grid(arr, H, EE, NN)
            samp[k] = gg
            ok0 = ok_ if ok0 is None else (ok0 & ok_)
        ok0 = ok0 & np.isfinite(samp["L"])
        d_ = ok0 & dune_prior
        if int(d_.sum()) < 500:
            continue
        take = ok0 & (g < best)
        good = True
        norm = {}
        for k in outs:
            ref = samp[k][d_]
            med = float(np.median(ref))
            mad = float(np.median(np.abs(ref - med)))
            if not (mad > 0):
                good = False
                break
            norm[k] = (samp[k] - med) / (1.4826 * mad)
        if not good:
            continue
        for k in outs:
            outs[k] = np.where(take, norm[k], outs[k])
        best = np.where(take, g, best)
        used += 1
    ok = np.isfinite(outs["L"])
    if not ok.any():
        return None, None, None, None, None
    return (outs["L"], outs["BR"], outs["S"], ok,
            float(np.median(best[ok])))


def _vp2_surface(date, H, m41, EE, NN, dune_prior):
    """One vp2 frame as three normalised surfaces, through the SHARED transform.

    THE PAIR NEEDS NO ALIGNMENT, and that is the whole reason this exists. Every
    vp2 frame is read through one homography — phase-correlating the series
    against `site24-3-2021.png` returns (0, 0) px, and the markers-ON/OFF twins
    sampled to the ground grid through it agree at r = 0.994 — so two vp2 dates
    are already in register with each other by construction. The tile version of
    this had to search for a shift and never found one, because the tile
    transforms are independently fitted and (2026-09-12) wrong.

    Measured for scale: two different vp2 dates through this transform correlate
    at r = 0.342 over the warren, against 0.09 for two tiles of ONE date. The
    vp2 series is the comparable one.
    """
    from PIL import Image                                    # noqa: PLC0415
    man = pd.read_csv(MANIFEST, float_precision="round_trip")
    m = man[(man["imagery_date"].astype(str) == date)
            & (man["viewpoint"].astype(str).str.startswith("vp2"))
            & (man["role"] == "measurement")]
    if not len(m):
        return None, None, None, None, None, None
    fp = m41.AERIAL_DIR / str(m["filename"].iloc[0])
    if not fp.exists():
        return None, None, None, None, None, None
    a = np.asarray(Image.open(fp).convert("RGB")).astype(float)
    mx = a.max(axis=2)
    chans = {
        "L": 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2],
        "BR": a[:, :, 2] - a[:, :, 0],
        "S": np.where(mx > 0, (mx - a.min(axis=2)) / np.maximum(mx, 1.0), 0.0)
        * 100.0,
    }
    out, ok = {}, None
    for k, arr in chans.items():
        gg, ok_ = m41._sample_to_grid(arr, H, EE, NN)
        out[k] = gg
        ok = ok_ if ok is None else (ok & ok_)
    ok = ok & np.isfinite(out["L"])
    d_ = ok & dune_prior
    if int(d_.sum()) < 500:
        return None, None, None, None, None, None
    for k in list(out):
        ref = out[k][d_]
        med = float(np.median(ref))
        mad = float(np.median(np.abs(ref - med)))
        if not (mad > 0):
            return None, None, None, None, None, None
        out[k] = (out[k] - med) / (1.4826 * mad)
    rg = pd.read_csv(REPO / "outputs" / "41_canopy_cover"
                     / "41_03_registration.csv", float_precision="round_trip")
    rg = rg[rg["frame"] == VP2_REFERENCE_FRAME]
    gsd = float(rg["gsd_m"].iloc[0]) if len(rg) else float("nan")
    return out["L"], out["BR"], out["S"], ok, gsd, str(m["filename"].iloc[0])


def _align(a, aok, b, bok, stable, shift):
    """Integer-cell shift of `a` that best matches `b` ON GROUND THAT DID NOT CHANGE.

    DIFFERENCING TWO DATES NEEDS THEM ALIGNED BETTER THAN THE FEATURES BEING
    MEASURED, and the registrations carry 1.3-2.5 m on a 2 m grid. Unaligned,
    every slope edge appears as change and reads as water, which would be the
    most plausible-looking wrong answer this project has produced yet.

    The alignment is fitted on `stable` — the warren LESS every mapped hollow —
    because that is the ground the water cannot have moved. Fitting it on the
    whole frame would let the water itself pull the registration, which is
    circular. Whole cells only: sub-cell resampling would smooth the very
    contrast being measured.
    """
    best = (np.inf, 0, 0, 0)
    for dy in range(-shift, shift + 1):
        for dx in range(-shift, shift + 1):
            A = np.roll(np.roll(a, dy, axis=0), dx, axis=1)
            Ao = np.roll(np.roll(aok, dy, axis=0), dx, axis=1)
            m = Ao & bok & stable
            n = int(m.sum())
            if n < 5000:
                continue
            # MEDIAN ABSOLUTE DIFFERENCE, not correlation: the surfaces are
            # already z-scaled, so what matters is how closely they coincide,
            # and a median is not led by the few cells that genuinely changed.
            v = float(np.median(np.abs(A[m] - b[m])))
            if v < best[0]:
                best = (v, dx, dy, n)
    return best


def phase11(wet=None, dry=None, shift=3, series="tiles") -> int:
    """Bi-temporal change detection: the wettest date against a dry one.

    MARTIN'S DESIGN (2026-09-12), and it is the right one because of what it
    makes the reference. Phase 8 referenced a frame against the warren's open
    dune and phase 10 referenced a slack against its own rim; both failed on the
    2026-09-12 tiles, and both failed for the same reason — at 1 m the sand
    varies as much as sand differs from water, so no spatial reference is quiet
    enough. **Here the reference is THE SAME GROUND AT ANOTHER DATE.** The dune
    texture is in both images, so it cancels on differencing instead of having to
    be averaged away.

    THE PAIR IS CHOSEN FOR TEMPORAL PROXIMITY AND SEASON, not for resolution.
    2020-04-24 is the nearest dry date to 2021-03-24 — eleven months — and the
    same season, so sun elevation and vegetation phase are close and the
    difference is dominated by water rather than by phenology. It costs
    resolution: 2020-04-24 is 2.04 m/px median with nothing at or below 1.6 m, so
    the pair is a 2 m comparison even though the wet date holds 1.06 m. A
    difference is only as good as its coarser half.

    TWO-SIDED, for the glare Martin saw on the pools: water is where the wet date
    DIFFERS from the dry one — darker, or brighter and desaturated — not where it
    is dark.

    AND THE CONTROL IS A DRY PAIR. Differencing two dry dates must return
    essentially nothing. If it returns water, the method is detecting change that
    is not water — vegetation, a scrape, stale imagery, misalignment — and no
    number from the wet pair may be quoted. That test is run by
    `--dry <a> --dry <b>` with no wet date and is the strongest falsification this
    project has had available: it cannot be passed by construction, unlike a
    negative frame that never had the power to fail.
    """
    from rasterio.features import geometry_mask              # noqa: PLC0415
    from rasterio.transform import from_origin               # noqa: PLC0415
    from scipy import ndimage as ndi                         # noqa: PLC0415
    from shapely.geometry import shape as shapely_shape      # noqa: PLC0415

    from utils.config import (CANOPY_CHANGE_GRID_M,          # noqa: PLC0415
                              SLACK_MIN_AREA_M2)
    phase(11, "Change detection — the wet date against a dry one")

    if not wet or not dry:
        warn("give one --wet date and at least one --dry date")
        return 1
    hol_p = OUT / "W94_06_hollows.geojson"
    if not hol_p.exists():
        warn("phase 6 has not run: W94_06_hollows.geojson is missing")
        return 1
    hollows = gpd.read_file(hol_p).set_crs(OSGB, allow_override=True)
    if not TILE_CACHE.exists():
        warn(f"no tile transform cache at {TILE_CACHE.name}")
        return 1
    if series == "vp2":
        H, m41 = _vp2_transform()
        if H is None:
            return 1
        # NO ALIGNMENT SEARCH on vp2: the frames share one transform, so a shift
        # would be fitting noise. Searching anyway would let the water move the
        # registration, which is the error the tile version could not escape.
        shift = 0
    else:
        m41 = _m41_module()
        H = None

    res = float(CANOPY_CHANGE_GRID_M)
    minx, miny, maxx, maxy = hollows.total_bounds
    minx, miny = np.floor(minx / res) * res - 200.0, np.floor(miny / res) * res - 200.0
    maxx, maxy = np.ceil(maxx / res) * res + 200.0, np.ceil(maxy / res) * res + 200.0
    ge = np.arange(minx, maxx + res, res)
    gn = np.arange(maxy, miny - res, -res)
    EE, NN = np.meshgrid(ge, gn)
    gtr = from_origin(minx - res / 2, maxy + res / 2, res, res)
    hol_mask = geometry_mask(list(hollows.geometry), out_shape=EE.shape,
                             transform=gtr, invert=True)
    info(f"ground grid {EE.shape[1]} x {EE.shape[0]} at {res:.0f} m; "
         f"{series} imagery")

    # The common window, and the stable ground the alignment is fitted on.
    wm_w = geometry_mask([warren_on(wet)], out_shape=EE.shape, transform=gtr,
                         invert=True)
    if series == "tiles":
        stale_w, _ = _stale_cells(wet, m41, EE, NN, wm_w & ~hol_mask)
        Lw, Bw, Sw, okw, gw = _date_surface(wet, m41, EE, NN,
                                            wm_w & ~hol_mask & ~stale_w)
    else:
        stale_w = np.zeros(EE.shape, bool)
        Lw, Bw, Sw, okw, gw, fw = _vp2_surface(wet, H, m41, EE, NN,
                                               wm_w & ~hol_mask)
        if Lw is not None:
            info(f"{wet}: {fw}")
    if Lw is None:
        warn(f"{wet}: no usable frame")
        return 1
    info(f"{wet}: GSD {gw:.3f} m")

    rows = []
    for d0 in dry:
        step(f"{wet} against {d0}")
        wm_d = geometry_mask([warren_on(d0)], out_shape=EE.shape, transform=gtr,
                             invert=True)
        if series == "tiles":
            stale_d, _ = _stale_cells(d0, m41, EE, NN, wm_d & ~hol_mask)
            Ld, Bd, Sd, okd, gd = _date_surface(d0, m41, EE, NN,
                                                wm_d & ~hol_mask & ~stale_d)
        else:
            stale_d = np.zeros(EE.shape, bool)
            Ld, Bd, Sd, okd, gd, fd = _vp2_surface(d0, H, m41, EE, NN,
                                                   wm_d & ~hol_mask)
            if Ld is not None:
                info(f"  {d0}: {fd}")
        if Ld is None:
            warn(f"  {d0}: no usable frame")
            continue
        info(f"  {d0}: GSD {gd:.3f} m — the pair is a "
             f"{max(gw, gd):.2f} m comparison")
        stable = wm_w & wm_d & ~hol_mask & ~stale_w & ~stale_d
        # THE PAIR'S OWN CORRELATION OVER UNCHANGED GROUND IS THE GO/NO-GO, and
        # it is printed before any result. Two captures of one place must agree
        # there; the tile pairs managed r = 0.03 and everything downstream of
        # that was noise. A number here near zero means the pair cannot be
        # differenced, whatever the rest of the output says.
        m0 = okw & okd & stable
        r0 = (float(np.corrcoef(Lw[m0], Ld[m0])[0, 1]) if int(m0.sum()) > 5000
              else float("nan"))
        info(f"  the pair agrees on unchanged ground at r = {r0:+.3f} "
             f"({int(m0.sum())} cell(s))")
        if not np.isfinite(r0) or r0 < PAIR_MIN_R:
            warn(f"  THE PAIR DOES NOT AGREE ON GROUND THAT CANNOT HAVE CHANGED "
                 f"(r {r0:+.3f} < {PAIR_MIN_R}). Differencing them measures the "
                 f"registration, not the water. No result is written.")
            rows.append({"wet_date": wet, "dry_date": d0, "series": series,
                         "pair_r": round(r0, 4) if np.isfinite(r0) else None,
                         "verdict": "REFUSED - the pair does not co-register"})
            continue
        mad0, dx, dy, n = _align(Lw, okw, Ld, okd, stable, shift)
        if not np.isfinite(mad0):
            warn("  the two dates share too little stable ground to align")
            continue
        info(f"  aligned on {n} cell(s) of unchanged ground: shift "
             f"({dx * res:+.0f}, {-dy * res:+.0f}) m, residual median "
             f"|dz| {mad0:.3f}")
        if shift and (abs(dx) == shift or abs(dy) == shift):
            warn(f"  THE BEST SHIFT IS AT THE EDGE OF THE SEARCH — widen "
                 f"--shift; the alignment may not be the true one")

        def _sh(a):
            return np.roll(np.roll(a, dy, axis=0), dx, axis=1)

        A, Aok, AB, AS = _sh(Lw), _sh(okw), _sh(Bw), _sh(Sw)
        both = Aok & okd & wm_w & wm_d & ~stale_w & ~stale_d
        dL = np.where(both, A - Ld, np.nan)
        dS = np.where(both, AS - Sd, np.nan)
        # THE NOISE IS MEASURED FROM THE UNCHANGED GROUND, not assumed. Whatever
        # is left between two dates over dune that did not change IS this pair's
        # noise floor: exposure, phenology, residual misalignment, resampling.
        base = dL[both & ~hol_mask]
        base = base[np.isfinite(base)]
        nmed = float(np.median(base))
        nsd = 1.4826 * float(np.median(np.abs(base - nmed)))
        info(f"  noise floor from unchanged dune: median {nmed:+.3f}, robust sd "
             f"{nsd:.3f} over {base.size} cell(s)")
        if not (nsd > 0):
            warn("  the unchanged ground has no spread; cannot set a threshold")
            continue
        # A change of this many noise sd's is what counts. Stated, not tuned: the
        # same 3-sigma a spectroscopist would ask for, and the dry-pair control
        # below is what says whether it is enough.
        k = CHANGE_SIGMA
        zL = (dL - nmed) / nsd
        zS = (dS - np.nanmedian(dS[both & ~hol_mask])) / max(
            1.4826 * float(np.nanmedian(np.abs(
                dS[both & ~hol_mask]
                - np.nanmedian(dS[both & ~hol_mask])))), 1e-9)
        darker = np.isfinite(zL) & (zL <= -k)
        glare = np.isfinite(zL) & np.isfinite(zS) & (zL >= k) & (zS <= -k)
        changed = darker | glare
        cell_m2 = res * res
        min_cells = int(round(SLACK_MIN_AREA_M2 / cell_m2))
        lab, nn = ndi.label(changed)
        if nn:
            counts = np.bincount(lab.ravel())
            drop = counts < min_cells
            drop[0] = True
            lab = np.where(drop[lab], 0, lab)
        n_bodies = int(len(np.unique(lab)) - 1)
        area_ha = float((lab > 0).sum()) * cell_m2 / 1e4
        in_hol = float(((lab > 0) & hol_mask).sum()) * cell_m2 / 1e4
        info(f"  changed: {n_bodies} bod(ies) above {SLACK_MIN_AREA_M2:.0f} m2, "
             f"{area_ha:.2f} ha — {in_hol:.2f} ha inside a mapped hollow "
             f"({(in_hol / area_ha * 100 if area_ha else 0):.0f} %), "
             f"darker {float(darker.sum()) * cell_m2 / 1e4:.2f} ha, "
             f"glare {float(glare.sum()) * cell_m2 / 1e4:.2f} ha")

        row = {"wet_date": wet, "dry_date": d0, "series": series,
               "pair_r": round(r0, 4), "verdict": "READ",
               "gsd_pair_m": round(max(gw, gd), 3),
               "shift_e_m": dx * res, "shift_n_m": -dy * res,
               "align_resid": round(mad0, 4), "noise_sd": round(nsd, 4),
               "sigma": k, "n_bodies": n_bodies, "change_ha": round(area_ha, 3),
               "change_in_hollow_ha": round(in_hol, 3),
               "darker_ha": round(float(darker.sum()) * cell_m2 / 1e4, 3),
               "glare_ha": round(float(glare.sum()) * cell_m2 / 1e4, 3)}

        if lab.max() > 0:
            from rasterio.features import shapes              # noqa: PLC0415
            polys, ids = [], []
            for geom, val in shapes(lab.astype("int32"), mask=(lab > 0),
                                    transform=gtr):
                polys.append(shapely_shape(geom))
                ids.append(int(val))
            fg = gpd.GeoDataFrame({"body_id": ids}, geometry=polys, crs=OSGB)
            fg = fg.dissolve(by="body_id", as_index=False)
            fg["area_m2"] = fg.area.round(1)
            # ATTRIBUTION, not delineation — the hollow NAMES the body, exactly
            # as in phase 8. `_score` needs the column, and a change body that
            # names no hollow is a real category, not a gap to fill.
            jj = gpd.sjoin(fg[["body_id", "geometry"]],
                           hollows[["slack", "geometry"]], how="left",
                           predicate="intersects")
            jj = jj.drop_duplicates("body_id")[["body_id", "slack"]]
            fg = fg.merge(jj, on="body_id", how="left")
            fg["slack"] = fg["slack"].astype("Int64")
            q = OUT / f"W94_22_change_{wet}_vs_{d0}.geojson"
            q.write_text(fg.to_json(), encoding="utf-8")
            saved(q.name)
            # SCORED AGAINST THE WELLS, which is the only external check here.
            lev = pd.read_csv(REPO / "outputs" / "01_wells_clean.csv",
                              float_precision="round_trip")
            lev = lev.rename(columns={lev.columns[0]: "month"})
            lev["month"] = pd.to_datetime(lev["month"])
            wells = pd.read_csv(REPO / "outputs" / "01_well_elevations.csv",
                                float_precision="round_trip")
            sc = _score(fg, lev, wells, wet, gtr, both, 0.15, max(gw, gd))
            row.update(sc["summary"])
            if len(sc["per_well"]):
                p2 = OUT / f"W94_22_wells_{wet}_vs_{d0}.csv"
                sc["per_well"].to_csv(p2, index=False)
                saved(p2.name)
            info(f"  against the dipwells: recall {sc['summary']['recall']}, "
                 f"precision {sc['summary']['precision']}, agreement "
                 f"{sc['summary']['agreement']} at {sc['summary']['n_wells']} "
                 f"well(s)")
        rows.append(row)

    if not rows:
        warn("no pair produced a result")
        return 1
    D = pd.DataFrame(rows)
    p = OUT / "W94_22_change_pairs.csv"
    if p.exists():
        prev = pd.read_csv(p, float_precision="round_trip")
        key = set(zip(D["wet_date"].astype(str), D["dry_date"].astype(str)))
        prev = prev[[(a_, b_) not in key for a_, b_ in
                     zip(prev["wet_date"].astype(str),
                         prev["dry_date"].astype(str))]]
        D = pd.concat([prev, D], ignore_index=True)
    D.to_csv(p, index=False)
    saved(p.name)
    info("A DRY-AGAINST-DRY PAIR IS THE CONTROL. Run one, and read the wet "
         "pair's area against it: whatever a dry pair returns is this method's "
         "false positive, and the wet number is only worth the margin between "
         "them.")
    return 0


def _slack_floors(hollows, ds, bias_m):
    """Every slack's floor elevation from the DEM, debiased.

    THE DEM SUPPLIES THE FLOOR (Martin, 2026-09-13). Phase 9 offered three units
    and this is the first: the minimum DEM elevation inside the slack's own
    polygon. Two corrections are applied and both were measured, not assumed —
    the raster's local bias, from 35 waterline/well pairs in phase 9, and any
    ground cut by scraping AFTER the LiDAR was flown.
    """
    from rasterio.mask import mask as rio_mask                # noqa: PLC0415
    from utils.config import SCRAPE_DEM_CORRECTION_M          # noqa: PLC0415
    out = []
    for _, h in hollows.iterrows():
        if pd.isna(h.get("slack")):
            continue
        try:
            a, _ = rio_mask(ds, [h.geometry.__geo_interface__], crop=True,
                            filled=True, nodata=np.nan)
        except Exception:                                     # noqa: BLE001
            continue
        z = a[0][np.isfinite(a[0])]
        if ds.nodata is not None:
            z = z[z != ds.nodata]
        if z.size < 3:
            continue
        out.append({"slack": int(h["slack"]),
                    "floor_raw_m": round(float(np.nanmin(z)), 3),
                    "floor_m": round(float(np.nanmin(z)) - bias_m, 3),
                    "area_m2": round(float(h.geometry.area), 1),
                    "E": float(h.geometry.centroid.x),
                    "N": float(h.geometry.centroid.y)})
    return pd.DataFrame(out)


def _valid(g):
    """Geometry from a hand-drawn KML, made usable without changing what it says."""
    if g is None or g.is_empty:
        return g
    if not g.is_valid:
        try:
            from shapely.validation import make_valid            # noqa: PLC0415
            g = make_valid(g)
        except Exception:                                        # noqa: BLE001
            g = g.buffer(0)
    return g


def _bush_mask_geom():
    """The persistent bush layer: phase 19's, or Martin's hand mask, or both.

    Read fresh on every use rather than cached, so a redrawn KML takes effect on
    the next run without anything having to be invalidated.
    """
    from shapely.ops import unary_union                          # noqa: PLC0415
    parts = []
    for src in (OUT / "W94_95_bush_mask.geojson", BUSH_MASK_KML):
        if not src.exists():
            continue
        try:
            g = gpd.read_file(src).to_crs(OSGB)
        except Exception:                                        # noqa: BLE001
            continue
        u = _valid(unary_union([_valid(x) for x in g.geometry]))
        if u is not None and not u.is_empty:
            parts.append(u)
    if not parts:
        return None
    return _valid(unary_union(parts))


def _standing_water_geom():
    """Water present even in a dry frame — drinking pools. NEVER masked.

    Martin dug these out of the July 2019 imagery precisely because they are the
    one thing in a dry frame that IS water, and a mask that swallowed them would
    teach the classifier to ignore real standing water everywhere it occurs.
    """
    from shapely.ops import unary_union                          # noqa: PLC0415
    if not STANDING_WATER_KML.exists():
        return None
    g = gpd.read_file(STANDING_WATER_KML).to_crs(OSGB)
    return _valid(unary_union([_valid(x) for x in g.geometry]))


def _idw(xs, ys, vs, X, Y, power=2.0, eps=1e-6):
    """Inverse-distance interpolation of the water table, power 2.

    A dune water table is a smooth mound between wells, which is the case IDW is
    honest for; it is not honest about a surface with structure between its
    control points, and the leave-one-out error reported alongside is what says
    how much that matters here.
    """
    xs = np.asarray(xs, float)[:, None]
    ys = np.asarray(ys, float)[:, None]
    vs = np.asarray(vs, float)[:, None]
    d = np.sqrt((xs - np.asarray(X, float)[None, :]) ** 2
                + (ys - np.asarray(Y, float)[None, :]) ** 2) + eps
    wgt = 1.0 / d ** power
    return (wgt * vs).sum(axis=0) / wgt.sum(axis=0)


def _wet_cells(form, xs, ys, hh, ground_at_well, BE, BN, zb, EE, NN, Z,
               unit_ok, dem_at_bnd=None, ground_reg=None):
    """Where the water table stands above the ground, in one of two forms.

    ELEVATION FORM (the original): interpolate ground + h at the wells and
    compare the result with the cell's floor. A dune water table is a MOUND, and
    inverse-distance weighting pulls toward the mean of its control points away
    from them, so this under-predicts the head exactly where the mound stands
    highest. Phase 16 measured the consequence: the slacks it misses sit at a
    median floor of 9.10 m AOD against 4.17 m for those it gets.

    DEPTH FORM: interpolate h ALONE and add it to the DEM. The topography then
    comes from the raster, which knows it at 2 m, and the interpolator carries
    only the residual depth field — small, smooth, and the thing a dipwell
    actually measures. This is also the variable the SSM is written in (Martin,
    2026-09-13) and the one D-163 found the data prefer: a drainage base that
    follows the topography rather than a regional one.

    A SLACK'S WATER TABLE IS ONE LEVEL, NOT A FIELD. In the depth form it is
    evaluated at the unit's own floor — WT = floor + h(floor) — and the flooded
    cells are that slack's hypsometry below it. Comparing each cell against its
    OWN ground instead would not be a water surface at all, which is the error in
    the first quick test of this idea.

    The estuary boundary keeps its meaning in both: at the estuary the water
    table is z_b, so its depth below the local ground is z_b - DEM there.
    """
    if form == "elevation":
        wt = [g + h for g, h in zip(ground_at_well, hh)]
        X = np.concatenate([xs, BE]) if len(BE) else np.asarray(xs)
        Y = np.concatenate([ys, BN]) if len(BE) else np.asarray(ys)
        V = (np.concatenate([wt, np.full(len(BE), zb)]) if len(BE)
             else np.asarray(wt))
        surf = _idw(X, Y, V, EE, NN)
        wet = Z < surf
        return wet, (surf - Z)[wet]

    X = np.concatenate([xs, BE]) if len(BE) else np.asarray(xs)
    Y = np.concatenate([ys, BN]) if len(BE) else np.asarray(ys)
    V = (np.concatenate([hh, zb - np.asarray(dem_at_bnd)]) if len(BE)
         else np.asarray(hh))
    h_s = _idw(X, Y, V, EE, NN)
    # THE GROUND h IS MEASURED AGAINST IS THE REGIONAL SURFACE, NOT THE PIXEL.
    # A dipwell's h is its depth below the ground AT THE WELL, and the water
    # table between wells is nearly flat while the ground is not. Adding h to
    # the RAW DEM therefore drives the water surface down into every hollow it
    # crosses, and the construction collapses: measured, the wettest date
    # returns 4.67 ha and every dry control 0.00. Adding it to the DEM smoothed
    # at SURFACE_GROUND_SMOOTH_M keeps the mound the elevation form flattens
    # without inheriting the metre-scale roughness the water table does not
    # have. The smoothing length is a physical statement about the water-table
    # mound's scale and is swept in phase 17.
    wt = (ground_reg if ground_reg is not None else Z) + h_s
    wet = Z < wt
    return wet, (wt - Z)[wet]


def _fit_well(lev, climate, well, datum):
    """Fit one well at one datum, ONCE. The fit does not depend on the date, and
    refitting per date cost six times what the sweep needed."""
    from utils.model_utils import build_ssm_frame, fit_ssm    # noqa: PLC0415
    s = lev[well].dropna()
    if len(s) < 24:
        return None, None
    try:
        fr = build_ssm_frame(s, climate, drainage_datum=datum)
        fit = fit_ssm(pre_built_frame=fr, drainage_datum=datum)
    except Exception:                                         # noqa: BLE001
        return None, None
    return fr, fit


# The window whose climate sets the level a slack is standing at. Six months is
# a recharge season: flooding in March reflects the winter, not the fortnight.
EQUIL_MONTHS = 6


def _equilibrium_h(fr, fit, date, datum, months=EQUIL_MONTHS):
    """The level the recent climate SUSTAINS, which is where the datum shows.

    h* solves Delta_h = 0 for a given climate:

        0 = b1*P - b2*PET - b3*(DATUM + h*)   =>   h* = (b1*P - b2*PET)/b3 - DATUM

    WHY THIS EXISTS. The one-step-ahead prediction cannot see the datum at all,
    and that is structural rather than a defect of the data: beta_3 falls as
    roughly 1/DATUM, so the product beta_3*(DATUM + h_prev) that enters the
    equation is near-invariant — measured across a 2.0-5.0 m sweep it moves from
    0.2119 to 0.2031, under 5 %. It is the same cancellation that leaves Model B's
    beta_3 unchanged at every datum (D-109), and it made the first datum sweep
    flat to 0.002 in agreement.

    In h* the cancellation does not happen: beta_3 appears only in the
    denominator and DATUM subtracts on its own. Measured over 2.0-8.0 m of datum,
    h* moves about 0.30 m at a typical well — which is the scale that decides
    whether a slack floods, and so the scale the flood record can resolve.

    The climate is the mean over the preceding `months`, not the long-run mean:
    a March flood reflects the winter's recharge.
    """
    t = pd.Timestamp(date).to_period("M").to_timestamp()
    w = fr.loc[:t].tail(months)
    if len(w) < max(3, months // 2) or fit is None:
        return None
    b1 = fit.get("beta_1_recharge")
    b2 = fit.get("beta_2_atmospheric_draw")
    b3 = fit.get("beta_3_drainage")
    if None in (b1, b2, b3) or not b3 or b3 <= 0:
        return None
    return float((b1 * w["P"].mean() - b2 * w["PET"].mean()) / b3 - datum)


def _predict_from(fr, fit, date):
    """One-step-ahead prediction for one month, from an existing fit."""
    if fr is None or fit is None:
        return None
    t = pd.Timestamp(date).to_period("M").to_timestamp()
    if t not in fr.index:
        return None
    row = fr.loc[t]
    b1 = fit.get("beta_1_recharge")
    b2 = fit.get("beta_2_atmospheric_draw")
    b3 = fit.get("beta_3_drainage")
    if None in (b1, b2, b3):
        return None
    dh = (b1 * row["P"] - b2 * row["PET"] - b3 * row["h_disp_prev"])
    return {"h_pred": float(row["h_prev"] + dh), "h_obs": float(row["h"]),
            "beta_1_recharge": float(b1), "beta_2_atmospheric_draw": float(b2),
            "beta_3_drainage": float(b3)}


def _predict_h(lev, climate, well, date, datum):
    """One-step-ahead SSM prediction of h for one well in one month.

    ONE-STEP-AHEAD, NOT FREE-RUN. A free run from the start of the record would
    accumulate drift, and the drift — not the datum — would be what the sweep
    measured. The previous month's OBSERVED level is used, which is what the
    model's own predictive form does.
    """
    from utils.model_utils import build_ssm_frame, fit_ssm    # noqa: PLC0415
    s = lev[well].dropna()
    if len(s) < 24:
        return None
    try:
        fr = build_ssm_frame(s, climate, drainage_datum=datum)
        fit = fit_ssm(pre_built_frame=fr, drainage_datum=datum)
    except Exception:                                         # noqa: BLE001
        return None
    if fit is None:
        return None
    t = pd.Timestamp(date).to_period("M").to_timestamp()
    if t not in fr.index:
        return None
    row = fr.loc[t]
    b1 = fit.get("beta_1_recharge")
    b2 = fit.get("beta_2_atmospheric_draw")
    b3 = fit.get("beta_3_drainage")
    if None in (b1, b2, b3):
        return None
    dh = (b1 * row["P"] - b2 * row["PET"] - b3 * row["h_disp_prev"])
    return {"h_pred": float(row["h_prev"] + dh), "h_obs": float(row["h"]),
            "beta_1_recharge": float(b1), "beta_2_atmospheric_draw": float(b2),
            "beta_3_drainage": float(b3)}


def phase12(dates=None, datums=None, mode="step") -> int:
    """Predicted flood extent from the SSM, and a test of DRAINAGE_DATUM.

    THE CHAIN. The SSM predicts head from climate; head plus ground gives a
    water-table elevation at each well; inverse-distance interpolation makes that
    a surface; a slack floods where the surface stands above its floor. Summed,
    that is a predicted flooded area for any month in the record — which is what
    D-159 set out to produce.

    AND THE DATUM IS TESTABLE THROUGH IT. `DRAINAGE_DATUM` is a free parameter
    that nothing outside the fit constrains, and under Model A it is not inert:
    with no intercept it redistributes across beta_1, beta_2 and beta_3 (D-007,
    D-109). **Flooding is the high-water extreme, which is exactly where
    beta_3 * h_disp_prev is largest**, so the flood record constrains the datum
    more sharply than the fit itself, which is dominated by mid-range months.

    THE SCORING IS ON UNGAUGED SLACKS ONLY, and that is the whole point. The SSM
    is fitted on the dipwells, so a gauged slack tests almost nothing — the model
    has seen its water level. The imagery reaches ground the network does not,
    and those slacks are the only independent observations available.

    Both imagery observables are scored, because they fail in opposite
    directions: the per-slack classification (phase 10, precision 1.000, recall
    0.438) and the flood polygons (phase 8). The classification's recall deficit
    caps absolute agreement; it does NOT affect the ranking across the sweep,
    because the same deficit applies at every datum — so the curve is readable
    where the absolute number is not.

    WHAT WOULD FALSIFY THE TEST, stated before it is run: a flat curve (the
    flood record does not constrain the datum); the two observables preferring
    datums more than one step apart (they are measuring different things); an
    optimum at either end (the range is wrong); or a negative cluster beta_3 at
    the chosen datum, which D-007 says means the datum is wrong.

    NOTHING IS WRITTEN TO config.py. This reports a curve; moving the datum is a
    decision with consequences across beta_1, beta_2, beta_3, t-half and D-109's
    tabulation, and it belongs in a D-entry.
    """
    from shapely.geometry import Point                        # noqa: PLC0415

    from utils.config import DRAINAGE_DATUM                   # noqa: PLC0415
    phase(12, "Predicted flood extent, and the datum test")

    hol_p = OUT / "W94_06_hollows.geojson"
    if not hol_p.exists():
        warn("phase 6 has not run")
        return 1
    hollows = gpd.read_file(hol_p).set_crs(OSGB, allow_override=True)
    wells = pd.read_csv(REPO / "outputs" / "01_well_elevations.csv",
                        float_precision="round_trip")
    lev = pd.read_csv(REPO / "outputs" / "01_wells_clean.csv",
                      float_precision="round_trip")
    lev = lev.rename(columns={lev.columns[0]: "month"})
    lev["month"] = pd.to_datetime(lev["month"])
    lev = lev.set_index("month")
    from utils.paths import INT_CLIMATE                        # noqa: PLC0415
    climate = pd.read_csv(INT_CLIMATE, float_precision="round_trip")
    c0 = climate.columns[0]
    climate[c0] = pd.to_datetime(climate[c0])
    climate = climate.set_index(c0)

    # ── floors ──────────────────────────────────────────────────────────────
    ds = rasterio.open(DATA_DEM)
    F = _slack_floors(hollows, ds, PHASE9_DEM_BIAS_M)
    ds.close()
    if not len(F):
        warn("no slack floor could be measured")
        return 1
    en = {str(n).lower(): (float(e), float(nn)) for n, e, nn
          in zip(wells["Name"], wells["E"], wells["N"])}
    ground = {str(n).lower(): float(g) for n, g
              in zip(wells["Name"], wells["ground_elev_m"])}
    gp = gpd.GeoDataFrame(
        {"well": list(en)}, geometry=[Point(*en[k]) for k in en], crs=OSGB)
    j = gpd.sjoin_nearest(gp, hollows[["slack", "geometry"]],
                          max_distance=VP2_RESIDUAL_M, how="inner")
    gauged = {int(s) for s in j["slack"].dropna()}
    F["gauged"] = F["slack"].isin(gauged)
    p = OUT / "W94_30_slack_floors.csv"
    F.to_csv(p, index=False)
    saved(p.name)
    step(f"{len(F)} slack floor(s) from the DEM, bias {PHASE9_DEM_BIAS_M:+.3f} m "
         f"removed; {int(F['gauged'].sum())} hold a dipwell and are EXCLUDED "
         f"from scoring, {int((~F['gauged']).sum())} are independent")

    # ── the observed truth, from the imagery ────────────────────────────────
    obs = {}
    cpath = OUT / "W94_20_slack_contrast.csv"
    if cpath.exists():
        C = pd.read_csv(cpath, float_precision="round_trip")
        if "wet" in C.columns:
            for d_, g in C.groupby("date"):
                obs[str(d_)] = {int(r.slack): bool(r.wet)
                                for r in g.itertuples() if pd.notna(r.slack)}
    if not obs:
        warn("no phase 10 classification with a `wet` column; run phase 10 "
             "without --calibrate first")
        return 1
    dts = sorted(obs) if not dates else [d for d in sorted(obs) if d in set(dates)]
    dts = [d for d in dts if any(obs[d].values())]
    if not dts:
        warn("no date with any slack classified wet; nothing to score against")
        return 1
    info(f"scoring against {len(dts)} date(s): {', '.join(dts)}")

    sweep = datums or list(np.round(np.arange(2.0, 8.01, 0.5), 2))
    if DRAINAGE_DATUM not in sweep:
        sweep = sorted(set(sweep) | {float(DRAINAGE_DATUM)})
    info(f"datum sweep: {sweep[0]:.1f} to {sweep[-1]:.1f} m, "
         f"{len(sweep)} value(s); committed is {DRAINAGE_DATUM:.1f}")
    info(f"prediction mode: {mode}"
         + ("  — the level the preceding "
            f"{EQUIL_MONTHS} months of climate sustains, which is where the "
            "datum shows" if mode == "equilibrium"
            else "  — one month ahead from the observed previous level; NOTE "
                 "this mode is structurally blind to the datum, see "
                 "_equilibrium_h"))

    rows, detail = [], []
    for datum in sweep:
        preds, b3s = {}, []
        for w_ in wells["Name"]:
            k = str(w_)
            if k not in lev.columns or k.lower() not in ground:
                continue
            fr, fit = _fit_well(lev, climate, k, datum)
            if fit is None:
                continue
            b3 = fit.get("beta_3_drainage")
            if b3 is not None:
                b3s.append(float(b3))
            for d_ in dts:
                r = _predict_from(fr, fit, d_)
                if r is None:
                    continue
                if mode == "equilibrium":
                    he = _equilibrium_h(fr, fit, d_, datum)
                    if he is None:
                        continue
                    r = dict(r, h_pred=he)
                preds.setdefault(d_, {})[k.lower()] = r
        if not preds:
            continue
        agree = {}
        for d_ in dts:
            pw = preds.get(d_, {})
            if len(pw) < 8:
                continue
            xs = [en[k][0] for k in pw]
            ys = [en[k][1] for k in pw]
            wt = [ground[k] + v["h_pred"] for k, v in pw.items()]
            # LEAVE-ONE-OUT: the interpolation's own error, at the only places
            # it can be checked. Reported per datum so a good agreement bought
            # by a bad surface is visible.
            loo = []
            for i in range(len(xs)):
                m = [q for q in range(len(xs)) if q != i]
                if len(m) < 5:
                    continue
                v = _idw([xs[q] for q in m], [ys[q] for q in m],
                         [wt[q] for q in m], [xs[i]], [ys[i]])[0]
                loo.append(abs(v - wt[i]))
            G = F[~F["gauged"]]
            surf = _idw(xs, ys, wt, G["E"].values, G["N"].values)
            pred_wet = surf > G["floor_m"].values
            truth = np.array([obs[d_].get(int(s), False) for s in G["slack"]])
            tp = int((pred_wet & truth).sum())
            fp = int((pred_wet & ~truth).sum())
            fn = int((~pred_wet & truth).sum())
            tn = int((~pred_wet & ~truth).sum())
            n = tp + fp + fn + tn
            agree[d_] = {
                "tp": tp, "fp": fp, "fn": fn, "tn": tn,
                "agreement": (tp + tn) / n if n else None,
                "recall": tp / (tp + fn) if tp + fn else None,
                "precision": tp / (tp + fp) if tp + fp else None,
                "pred_ha": float(G.loc[pred_wet, "area_m2"].sum()) / 1e4,
                "loo_m": float(np.median(loo)) if loo else None,
                "n_wells": len(pw)}
            detail.append({"datum": datum, "date": d_, **agree[d_]})
        if not agree:
            continue
        ok = [v for v in agree.values() if v["agreement"] is not None]
        rows.append({
            "datum_m": datum,
            "beta_3_median": round(float(np.median(b3s)), 5) if b3s else None,
            "loo_m": (round(float(np.median([v["loo_m"] for v in ok
                                             if v["loo_m"] is not None])), 3)
                      if ok else None),
            "agreement": round(float(np.mean([v["agreement"] for v in ok])), 4),
            "recall": round(float(np.mean([v["recall"] for v in ok
                                           if v["recall"] is not None])), 4),
            "pred_ha": round(float(np.mean([v["pred_ha"] for v in ok])), 2),
            "n_dates": len(ok)})
        r = rows[-1]
        info(f"  datum {datum:4.1f} m: beta_3 median {r['beta_3_median']}, "
             f"LOO {r['loo_m']} m, predicted {r['pred_ha']:6.2f} ha, "
             f"agreement {r['agreement']:.3f}, recall {r['recall']:.3f}")

    if not rows:
        warn("the sweep produced nothing — no well could be fitted and predicted")
        return 1
    S = pd.DataFrame(rows)
    p = OUT / "W94_31_datum_sweep.csv"
    S.to_csv(p, index=False)
    saved(p.name)
    if detail:
        p2 = OUT / "W94_32_predicted_flood_by_date.csv"
        pd.DataFrame(detail).to_csv(p2, index=False)
        saved(p2.name)

    # ── read the curve, and refuse to over-read it ──────────────────────────
    best = S.loc[S["agreement"].idxmax()]
    span = float(S["agreement"].max() - S["agreement"].min())
    step(f"best agreement {best['agreement']:.3f} at datum "
         f"{best['datum_m']:.1f} m (committed {DRAINAGE_DATUM:.1f} m); "
         f"the curve spans {span:.3f}")
    if span < DATUM_CURVE_MIN_SPAN:
        warn(f"  THE CURVE IS FLAT ({span:.3f} < {DATUM_CURVE_MIN_SPAN}). The "
             f"flood record does not constrain the datum on this evidence, and "
             f"nothing should be concluded from the least-bad value.")
    if best["datum_m"] in (S["datum_m"].min(), S["datum_m"].max()):
        warn("  THE OPTIMUM IS AT AN END OF THE SWEEP — widen the range before "
             "reading anything from it.")
    if S["beta_3_median"].min() is not None and S["beta_3_median"].min() <= 0:
        warn("  a non-positive median beta_3 appears in the sweep — D-007 says "
             "that datum is wrong, whatever it scores")
    info("NOTHING IS WRITTEN TO config.py. Moving DRAINAGE_DATUM changes "
         "beta_1, beta_2, beta_3, t-half and D-109's tabulation, and is a "
         "decision for a D-entry.")
    return 0


_TREE_CACHE = {}


def _slack_units(site, bias_m, depth_m=None, area_m2=None, quiet=False):
    """The slack inventory, from the merge tree rather than from the hollows.

    WHY NOT THE PHASE 6 HOLLOWS. A hollow is whatever the delineation closed
    around, and at Newborough that includes composite basins and the estuarine
    flat: measured 2026-09-13, one "hollow" was 16.5 ha, and three features
    accounted for 25 of the 40 ha of flooding a dry control returned. A 16 ha
    slack is not a slack. The whole-hollow DEM minimum inherits the same fault —
    it sits a median 0.474 m below the well's own ground against phase 9's
    independently measured Delta of 0.140 m, and the gap grows with hollow area
    (r = +0.447), which is the signature of a composite.

    SO THE UNITS COME FROM THE MERGE TREE, which is the project's own tool for
    deciding what counts as a distinct basin: each cell is assigned to the
    SMALLEST CLOSED ancestor that still holds SLACK_MIN_DEPTH_M. Composites split
    at their saddles, and the 72,309 OPEN nodes — those whose subtree reaches the
    grid edge, so they drain away rather than holding water — are excluded
    outright. That is what removes the estuarine flat, and it removes it for a
    reason rather than by an area cap: a basin that drains to the sea is not a
    slack. Measured: 3,978 units above SLACK_MIN_AREA_M2, 71.5 ha, largest 0.2 ha.
    """
    from utils.config import SLACK_MIN_AREA_M2, SLACK_MIN_DEPTH_M  # noqa: PLC0415
    from utils.slacks import merge_tree                         # noqa: PLC0415
    from rasterio.features import geometry_mask                 # noqa: PLC0415

    # THE TREE DOES NOT DEPEND ON THE THRESHOLDS, only the selection off it
    # does, so a depth sweep rebuilds nothing. Cached on the mask and the bias,
    # which are what the tree is actually a function of.
    depth = SLACK_MIN_DEPTH_M if depth_m is None else float(depth_m)
    area = SLACK_MIN_AREA_M2 if area_m2 is None else float(area_m2)
    ckey = (hash(site.wkb), round(float(bias_m), 6))

    if ckey in _TREE_CACHE:
        arr, tr, leafc, par, fl, ml, op, n = _TREE_CACHE[ckey]
    else:
        arr, tr, leafc, par, fl, ml, op, n = _build_tree(site, bias_m)
        _TREE_CACHE[ckey] = (arr, tr, leafc, par, fl, ml, op, n)

    dep = np.where(op, -1.0, ml - fl)
    pick = np.full(n, -1, dtype=np.int64)
    for i in range(n):
        cur = i
        for _ in range(200):
            if (not op[cur]) and dep[cur] >= depth:
                pick[i] = cur
                break
            nxt = int(par[cur])
            if nxt < 0 or nxt == cur:
                break
            cur = nxt
    unit = pick[leafc]
    inside = geometry_mask([site], out_shape=arr.shape, transform=tr,
                           invert=True)
    unit = np.where(inside, unit, -1)
    res = abs(tr.a)
    uids, counts = np.unique(unit[unit >= 0], return_counts=True)
    keep = uids[counts * res * res >= area]
    ok = np.isin(unit, keep) & (unit >= 0)
    if not quiet:
        info(f"{n} merge-tree node(s), {int(op.sum())} open (draining to the "
             f"edge — not slacks); {len(uids)} unit(s), {len(keep)} above "
             f"{area:.0f} m2 at depth >= {depth:.2f} m, "
             f"{ok.sum() * res * res / 1e4:.1f} ha")
    return arr, unit, ok, tr, res


def _build_tree(site, bias_m):
    """The merge tree for one warren mask, which the thresholds then select off."""
    from utils.slacks import merge_tree                         # noqa: PLC0415

    ds = rasterio.open(DATA_DEM)
    db, b = ds.bounds, site.bounds
    rb = (max(b[0], db.left), max(b[1], db.bottom),
          min(b[2], db.right), min(b[3], db.top))
    win = rasterio.windows.from_bounds(*rb, ds.transform)
    arr = ds.read(1, window=win).astype("float32")
    tr = ds.window_transform(win)
    nod = ds.nodata
    ds.close()
    if nod is not None:
        arr = np.where(arr == nod, np.nan, arr)
    # merge_tree needs a finite DEM; nodata is raised above every real elevation
    # so it can never be a basin floor and never joins one.
    arr = np.where(np.isfinite(arr), arr, np.nanmax(arr) + 50.0) - bias_m

    leafc, nodes = merge_tree(arr)
    n = len(nodes)
    par = np.fromiter((q["parent"] for q in nodes), dtype=np.int64, count=n)
    fl = np.fromiter((q["floor_m"] for q in nodes), dtype=float, count=n)
    ml = np.fromiter((q["merge_level_m"] for q in nodes), dtype=float, count=n)
    op = np.fromiter((q["open"] for q in nodes), dtype=bool, count=n)
    return arr, tr, leafc, par, fl, ml, op, n


def _model_flood_kml(date, EE, NN, wet, res, path):
    """The model's predicted flood, as KML, so it can be judged ON the imagery.

    A number cannot be argued with usefully and a matplotlib frame is not the
    photograph. This writes what the model says is under water as polygons in
    WGS84, to be opened in Google Earth on that date's own imagery at full
    resolution — which is the only comparison that settles whether the model is
    missing water or the read is over-reading it.
    """
    from shapely.geometry import box                           # noqa: PLC0415
    from shapely.ops import unary_union                        # noqa: PLC0415

    if not wet.any():
        return None
    h = res / 2.0
    cells = [box(x - h, y - h, x + h, y + h)
             for x, y in zip(EE[wet], NN[wet])]
    g = gpd.GeoDataFrame(geometry=[unary_union(cells)], crs=OSGB)
    g = g.explode(index_parts=False).to_crs(4326)
    k = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
         f"<name>model flood {date}</name>",
         '<Style id="mw"><LineStyle><color>ff9c3c1f</color><width>1</width>'
         '</LineStyle><PolyStyle><color>7fb46f1f</color></PolyStyle></Style>']
    for geom in g.geometry:
        ring = ""
        for poly in (list(geom.geoms) if geom.geom_type == "MultiPolygon"
                     else [geom]):
            cc = " ".join(f"{x:.7f},{y:.7f},0"
                          for x, y in poly.exterior.coords)
            ring += ("<Polygon><outerBoundaryIs><LinearRing><coordinates>"
                     f"{cc}</coordinates></LinearRing></outerBoundaryIs>"
                     "</Polygon>")
        k.append(f"<Placemark><styleUrl>#mw</styleUrl>{ring}</Placemark>")
    k.append("</Document></kml>")
    path.write_text("\n".join(k), encoding="utf-8")
    return len(g)


def _level_frame():
    """The monthly level frame, preferring the UNTHRESHOLDED one.

    `01_wells_clean.csv` is cut at Script 01's MIN_MONTHS_THRESH, which is an
    admission criterion for the clustering and the SSM. Phase 13 fits nothing —
    it interpolates OBSERVED head — so the threshold costs it five DGPS-surveyed
    south-eastern wells (D31, D33, D34, D39, D45; 17-18 months, 2010-03 to
    2011-08) in the one part of the site where the long-record network has no
    well. `01_wells_all.csv` (Script 01 >= 1.16.0) carries the same cleaning and
    bucketing with no threshold. Falls back with a warning so the tool still runs
    against an older tree.
    """
    pth = REPO / "outputs" / "01_wells_all.csv"
    if not pth.exists():
        warn("  01_wells_all.csv absent (Script 01 < 1.16.0); falling back to "
             "01_wells_clean.csv — the south-eastern wells will be missing")
        pth = REPO / "outputs" / "01_wells_clean.csv"
    lev = pd.read_csv(pth, float_precision="round_trip")
    lev = lev.rename(columns={lev.columns[0]: "month"})
    lev["month"] = pd.to_datetime(lev["month"])
    return _merge_calibration(lev)


def _merge_calibration(lev):
    """Overlay readings the pipeline's raw inputs do not yet contain.

    A flood frame needs the dipwell month it was taken in, and the pipeline's
    inputs are frozen earlier. These readings therefore live in
    `data/flood_calibration_levels.csv`, OUTSIDE the pipeline, and are merged
    here and nowhere else — see the note on DATA_FLOOD_CAL_LEVELS in paths.py for
    why that boundary is load-bearing rather than tidy.

    Bucketing is Script 01's: a reading on day > 15 belongs to that month, day
    <= 15 to the previous one. An existing month is NOT overwritten — the
    pipeline's own value wins wherever it has one, so this can only add.
    """
    from utils.paths import DATA_FLOOD_CAL_LEVELS                # noqa: PLC0415

    if not DATA_FLOOD_CAL_LEVELS.exists():
        return lev
    C = pd.read_csv(DATA_FLOOD_CAL_LEVELS, float_precision="round_trip")
    if not len(C):
        return lev
    d = pd.to_datetime(C["date"])
    mo = d.where(d.dt.day > 15, d - pd.offsets.MonthBegin(1))
    C["month"] = pd.to_datetime(
        mo.dt.year.astype(str) + "-" + mo.dt.month.astype(str).str.zfill(2)
        + "-01")
    have = set(lev["month"])
    added = 0
    for month, g in C.groupby("month"):
        if month in have:
            continue
        row = {"month": month}
        for _, r in g.iterrows():
            w = str(r["well"])
            if w in lev.columns:
                row[w] = float(r["h_m"])
        lev = pd.concat([lev, pd.DataFrame([row])], ignore_index=True)
        added += 1
        info(f"  calibration month {month:%Y-%m} added from "
             f"{DATA_FLOOD_CAL_LEVELS.name}: {len(row) - 1} well(s) — NOT a "
             f"pipeline input, and no pipeline number moves")
    if added:
        lev = lev.sort_values("month").reset_index(drop=True)
    return lev


def _estuary_control(site):
    """Pseudo-control points along the tidal boundary, held at a fixed level.

    MARTIN'S DESIGN (2026-09-13), and it is a boundary condition rather than a
    patch. The aquifer discharges to the Malltraeth estuary, so the water table
    is pinned near tide level along that margin; inverse-distance weighting has
    no way to know that and holds the surface up at the inland wells' level all
    the way to the shore. Measured before the boundary was added, a dry control
    returned 20.85 ha of flooding concentrated in one band on the estuary-facing
    flank — ground at 2.76-5.42 m AOD where the nearest wells sit inland and
    higher, and where five surveyed wells (D31, D33, D34, D39, D45, at 2.75-4.61 m) are
    absent from `01_wells_clean.csv` — NOT for want of readings. CORRECTED
    2026-09-13 (Martin): all five carry 17-18 months of measured head
    (2010-03 to 2011-08) in the raw record; Script 01's MIN_MONTHS_THRESH and
    MIN_EXTENDED_MONTHS, both SSM/clustering admission criteria, drop them from
    every emitted file. `pe` was never missing at all — it is in the extended
    network. Script 01 >= 1.16.0 emits `01_wells_all.csv` for exactly this, and
    `_level_frame()` prefers it, so on the one read date inside their record the
    boundary condition is replaced by measurement.

    The alternative considered and rejected was a distance cap: it improved the
    dry/wet ratio by discarding that flank on EVERY date, including the dates
    when its flooding is real, and it threw away a fifth of the warren to do it.
    """
    from shapely.geometry import MultiLineString                # noqa: PLC0415
    from utils.kml_io import read_kml                           # noqa: PLC0415
    p = DATA_GEO_DIR / f"{ESTUARY_KML}.kml"
    if not p.exists():
        warn(f"  {p.name} is missing; no boundary condition applied")
        return np.zeros(0), np.zeros(0)
    g = read_kml(p)
    if g.crs is None or g.crs.to_epsg() == 4326:
        g = g.set_crs("EPSG:4326", allow_override=True).to_crs(OSGB)
    E, N = [], []
    for geom in g.geometry:
        segs = list(geom.geoms) if isinstance(geom, MultiLineString) else [geom]
        for s in segs:
            for d in np.arange(0, s.length, ESTUARY_POINT_SPACING_M):
                q = s.interpolate(d)
                if site.buffer(ESTUARY_REACH_M).contains(q):
                    E.append(q.x)
                    N.append(q.y)
    return np.asarray(E), np.asarray(N)


def phase13(dates=None, z_b=None, kml=False, form="elevation") -> int:
    """Flooded extent: where the water table stands above the slack floor.

    MARTIN'S DEFINITION (2026-09-13): *"flooded means above slack floor"*. So the
    measurement is the DEM below an interpolated water table, cell by cell,
    inside slack units — not the imagery's "wet slack floor" (phase 8) and not
    its "open water" (phase 11), which are two different quantities and are the
    real reason those two reads differed sevenfold.

    THREE CORRECTIONS SEPARATE THIS FROM THE FIRST ATTEMPT, and each was measured
    rather than tuned:

      1. **Merge-tree slack units** in place of the phase 6 hollows, which
         removes composites and every basin that drains to the sea. See
         `_slack_units`.
      2. **The lake gauge is out of the interpolation.** `llyn rhos` is not a
         dipwell (it is the Llyn Rhos-Ddu lake gauge, outside the classified
         network) and it is the ONLY point at or above ground on both dry
         controls — so its presence made them look wet when no dipwell was.
      3. **The estuary as a boundary condition.** See `_estuary_control`.

    THE DRY CONTROLS ARE THE STANDING TEST, not a footnote. 2012-05-26 and
    2019-07-29 have ZERO dipwells at or above ground; whatever this returns on
    them is its false-positive floor, and no flooded area is worth more than the
    margin over it. Measured at z_b = 0 m AOD on the unthresholded frame: 2.71 and
    3.75 ha, against 17.00 ha on 2021-03-24 — and the series is monotonic in
    wet-well count across every date tested, which nothing before these
    corrections produced.

      4. **The unthresholded level frame** (`_level_frame`, Script 01 >= 1.16.0).
         Script 01's record-length thresholds are SSM and clustering admission
         criteria; an interpolation of observed head needs neither, and paid for
         them in the south-east. Recovering those wells cut the dry control on
         2010-05-27 from 4.49 to 2.15 ha and lifted the margin 3.5 -> 4.5 : 1.

    Z_B IS A PHYSICAL CHOICE AND IT IS NEARLY ADDITIVE. Raising it from 0 to 2 m
    AOD adds 6.9 ha to the wettest date and 5.3 ha to the driest, so it shifts
    every date together and changes no ranking. 0 m AOD is approximately mean sea
    level; a water table at a tidal margin usually sits a little above mean tide,
    so the defensible range runs from there towards MHW, at about +3.5 ha per
    metre.

    Z_B = 0 M AOD STANDS, AND THE MIDPOINT WAS TESTED RATHER THAN ASSUMED.
    Martin, 2026-09-13: *"set z_b at halfway from 0m to MHW if needed"*. The only
    tidal level in the corpus is MHWS ~ +2.9 m AOD (Caernarfon tide tables, cited
    in the Methods Supplement), so the midpoint is +1.45 m AOD. Measured from the
    pipeline's own `01_wells_all.csv`:

      | z_b        | worst dry control | wettest date | margin  |
      | 0.00 m AOD |           3.75 ha |    17.00 ha  | 4.5 : 1 |
      | 1.45 m AOD |           7.47 ha |    21.50 ha  | 2.9 : 1 |

    Raising it DOUBLES the false-positive floor and cuts the margin by a third,
    so it is not needed — which is itself the measured wells' doing. They pin the
    surface near the estuary at 1.96-2.79 m AOD (D45, 776 m from the coast), so
    the boundary no longer has to carry that flank and holding it higher only
    floods ground the readings say is dry. The ordering in wet-well count is
    monotonic at both levels, confirming z_b changes no ranking.
    """
    from utils.warren_mask import warren_on                     # noqa: PLC0415
    phase(13, "Flooded extent — water table above the slack floor")

    zb = ESTUARY_LEVEL_M_AOD if z_b is None else float(z_b)
    wells = pd.read_csv(REPO / "outputs" / "01_well_elevations.csv",
                        float_precision="round_trip")
    lev = _level_frame()
    ground = {str(n).lower(): float(g) for n, g
              in zip(wells["Name"], wells["ground_elev_m"])}

    dts = list(dates) if dates else list(DRY_CALIBRATION_DATES) + [
        "2021-03-24", "2021-04-04", "2020-03-31", "2017-03-24"]
    dts = sorted(set(dts))
    site = warren_on(max(dts))
    step("slack units from the merge tree")
    arr, unit, ok, tr, res = _slack_units(site, PHASE9_DEM_BIAS_M)
    rows_, cols_ = np.nonzero(ok)
    EE, NN = rasterio.transform.xy(tr, rows_, cols_)
    EE = np.asarray(EE)
    NN = np.asarray(NN)
    Z = arr[ok]
    cell_ha = res * res / 1e4

    BE, BN = _estuary_control(site)
    # The DEM under each boundary point, so the depth form can express z_b as a
    # depth below the local ground there.
    from scipy.ndimage import uniform_filter                 # noqa: PLC0415
    _k = max(1, int(round(SURFACE_GROUND_SMOOTH_M / res)))
    GS = uniform_filter(arr, size=_k, mode="nearest") if _k > 1 else arr
    GR = GS[rows_, cols_]
    DB = np.zeros(0)
    if len(BE):
        _rr, _cc = rasterio.transform.rowcol(tr, BE, BN)
        _rr = np.clip(np.asarray(_rr), 0, arr.shape[0] - 1)
        _cc = np.clip(np.asarray(_cc), 0, arr.shape[1] - 1)
        DB = GS[_rr, _cc]
    info(f"estuary boundary: {len(BE)} control point(s) at "
         f"{ESTUARY_POINT_SPACING_M:.0f} m along {ESTUARY_KML}.kml, held at "
         f"{zb:+.2f} m AOD")

    out = []
    for d in dts:
        wl = _well_levels(lev, wells, d)
        if wl is None or not len(wl):
            warn(f"  {d}: no dipwell month")
            continue
        xs, ys, hh, gw = [], [], [], []
        for _, r in wl.iterrows():
            k = str(r["well"]).lower()
            # THE LAKE GAUGE IS NOT A DIPWELL and must not set the water table.
            if k in ground and k != LAKE_GAUGE_NAME:
                xs.append(float(r["E"]))
                ys.append(float(r["N"]))
                hh.append(float(r["h_m"]))
                gw.append(ground[k])
        if len(xs) < MIN_WELLS_FOR_SURFACE:
            warn(f"  {d}: only {len(xs)} well(s); surface not computed")
            continue
        wet, dep = _wet_cells(form, xs, ys, hh, gw, BE, BN, zb, EE, NN, Z,
                              unit[ok], dem_at_bnd=DB, ground_reg=GR)
        n_wet_wells = int((wl[wl["well"].str.lower() != LAKE_GAUGE_NAME]["h_m"]
                           >= 0).sum())
        r_ = {"date": d, "form": form,
              "wells": len(xs), "wet_wells": n_wet_wells,
              "flooded_ha": round(float(wet.sum()) * cell_ha, 3),
              "median_depth_m": (round(float(np.median(dep)), 3)
                                 if dep.size else None),
              "units_flooded": int(len(np.unique(unit[ok][wet]))),
              "z_b_m_aod": zb,
              "dry_control": d in DRY_CALIBRATION_DATES}
        out.append(r_)
        if kml:
            q = OUT / f"W94_41_model_flood_{d}.kml"
            nk = _model_flood_kml(d, EE, NN, wet, res, q)
            if nk:
                saved(f"{q.name}  ({nk} polygon(s))")
        info(f"  {d}  {n_wet_wells:2d} wet dipwell(s)  "
             f"{r_['flooded_ha']:7.2f} ha  median depth "
             f"{r_['median_depth_m']}" + ("   [DRY CONTROL]" if r_["dry_control"]
                                          else ""))
    if not out:
        warn("no date produced a surface")
        return 1
    D = pd.DataFrame(out)
    p = OUT / "W94_40_flooded_extent.csv"
    if p.exists():
        prev = pd.read_csv(p, float_precision="round_trip")
        if "form" not in prev.columns:
            prev["form"] = "elevation"
        prev = prev[~(prev["date"].astype(str).isin(D["date"].astype(str))
                      & (prev["form"] == form))]
        D = pd.concat([prev, D], ignore_index=True)
    D = D.sort_values(["form", "date"])
    D.to_csv(p, index=False)
    saved(p.name)

    D = D[D["form"] == form]
    ctrl = D[D["dry_control"]]
    live = D[~D["dry_control"]]
    if len(ctrl):
        floor = float(ctrl["flooded_ha"].max())
        step(f"THE FALSIFICATION TEST: the dry controls return "
             f"{ctrl['flooded_ha'].min():.2f}-{floor:.2f} ha with ZERO dipwells "
             f"at or above ground. That is the false-positive floor.")
        if len(live):
            best = float(live["flooded_ha"].max())
            info(f"  against {best:.2f} ha on the wettest date — a margin of "
                 + (f"{best / floor:.1f} to 1" if floor > 0
                    else "infinity: the dry controls return nothing"))
            if floor > 0 and best < floor * DRY_CONTROL_MIN_RATIO:
                warn(f"  THE MARGIN IS BELOW {DRY_CONTROL_MIN_RATIO}:1. No "
                     f"flooded area from this run should be quoted.")
    info("Every area here is NET OF NOTHING: the dry-control floor is not "
         "subtracted, because it is not known to be uniform across dates. Quote "
         "the area and the floor together.")
    return 0


def _series_panel(lev, ground):
    """The fixed well panel, and why the series is built on one.

    THE NETWORK TREBLES ACROSS THE RECORD — a median of 7 wells reporting in
    2005, 24-28 in 2006-07, 31-36 in 2008-09, and 73-80 from 2010 on. A series
    computed on whatever wells exist in each month therefore confounds any
    long-term signal with the history of when CEH installed dipwells, and the
    confound runs the same way as the science: more wells means a surface pinned
    in more places, changing both its level and its variance.

    THE FIX IS NEARLY FREE. Leave-one-out error of the IDW surface, measured
    over every month: a 25-well panel returns 0.613 m, a 57-well panel 0.521 m,
    and every available well 0.527 m. Surface quality SATURATES at about 55
    wells, so a fixed panel is as good as the full network and better behaved in
    its tail, while holding composition constant so a change in the series is a
    change in the water table. Returns the panel and the all-available column
    list; the run computes both and the pair is the sensitivity.
    """
    cols = [c for c in lev.columns
            if c != "month" and str(c).lower() in ground
            and str(c).lower() != LAKE_GAUGE_NAME]
    idx = pd.to_datetime(lev["month"])
    late = lev.loc[idx >= pd.Timestamp(SERIES_PANEL_START), cols]
    cov = late.notna().mean()
    panel = sorted(cov[cov >= SERIES_PANEL_MIN_COVERAGE].index)
    return panel, sorted(cols)


def _units_for(site, cache):
    """Slack units for this warren mask, built once per CANOPY EPOCH.

    The merge tree is the expensive part of phase 13 and it depends only on the
    mask, which changes when a forest group's canopy closes or is felled - four
    boundaries across the record, not 229. Keyed on the mask's own geometry so
    the cache cannot go stale against a mask it did not build.
    """
    key = hash(site.wkb)
    if key not in cache:
        cache[key] = _slack_units(site, PHASE9_DEM_BIAS_M)
    return cache[key]


def _series_frame(month, EE, NN, ok, wet, dep, area_ha, n_wells, site, out_dir,
                  so_far=None, weak=False, panel_n=None):
    """One map for one month, on a fixed extent so the frames register.

    Every frame carries its own month, area and well count burnt in, because a
    frame lifted out of an animation and shown on its own must still say what it
    is and what it rests on.
    """
    import matplotlib                                        # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                          # noqa: PLC0415
    from utils.config import (SITE_MAP_EAST_MAX,             # noqa: PLC0415
                              SITE_MAP_EAST_MIN, SITE_MAP_NORTH_MAX,
                              SITE_MAP_NORTH_MIN)
    from utils.map_utils import add_en_axes, load_dem_hillshade  # noqa: PLC0415

    fig, ax = plt.subplots(figsize=(7.6, 6.4))
    load_dem_hillshade(ax, DATA_GEO_DIR, alpha=0.55)
    gpd.GeoSeries([site], crs=OSGB).plot(ax=ax, facecolor="none",
                                         edgecolor="#08519c", lw=0.9, zorder=3)
    # ONE SOLID COLOUR, not a depth ramp. A shallow cell on a Blues ramp is
    # almost white against a grey hillshade, so a depth-coloured animation reads
    # as water appearing and disappearing rather than spreading. Depth is in the
    # CSV, where it can be read properly; the frame answers "where", not "how
    # deep".
    if wet.any():
        ax.scatter(EE[wet], NN[wet], c=SERIES_WATER_COLOUR,
                   s=SERIES_FRAME_CELL_PT, marker="s", linewidths=0, zorder=4)
    ax.set_xlim(SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX)
    ax.set_ylim(SITE_MAP_NORTH_MIN, SITE_MAP_NORTH_MAX)
    add_en_axes(ax)
    ax.set_title(f"{month:%b %Y}   —   {area_ha:.2f} ha flooded   "
                 f"({n_wells} wells)", loc="left", fontsize=12)
    # THE CAVEAT TRAVELS WITH THE PICTURE (Martin, 2026-09-13). A frame will be
    # lifted out of the animation and shown on its own, so a month computed on a
    # part-reporting network says so on its own face rather than in a caption
    # somebody else writes.
    if weak:
        ax.text(0.5, 0.972,
                f"REDUCED NETWORK — {n_wells} of {panel_n} panel wells "
                f"reporting; indicative only",
                transform=ax.transAxes, ha="center", va="top", fontsize=9,
                color="#8c2d04", zorder=8,
                bbox=dict(boxstyle="round,pad=0.35", facecolor="#fee6ce",
                          edgecolor="#e6550d", lw=0.8, alpha=0.95))
    ax.text(0.99, 0.01, "modelled water table above slack floor; "
            "net of nothing", transform=ax.transAxes, ha="right", va="bottom",
            fontsize=7, color="#555555")
    # THE SERIES SO FAR, drawn inside the frame. A map alone cannot say whether
    # this month is unusual; the strip grows as the animation plays, so each
    # frame carries its own context instead of needing a caption.
    if so_far is not None and len(so_far) > 1:
        ins = ax.inset_axes([0.045, 0.055, 0.42, 0.15])
        xs_ = list(range(len(so_far)))
        ins.fill_between(xs_, 0, so_far, color=SERIES_WATER_COLOUR, alpha=0.55,
                         lw=0)
        ins.plot(xs_, so_far, color=SERIES_WATER_COLOUR, lw=0.8)
        ins.scatter([xs_[-1]], [so_far[-1]], s=9, color="#08306b", zorder=5)
        ins.set_xlim(0, SERIES_STRIP_MONTHS)
        ins.set_ylim(0, SERIES_STRIP_HA_MAX)
        ins.set_yticks([0, SERIES_STRIP_HA_MAX])
        ins.set_yticklabels(["0", f"{SERIES_STRIP_HA_MAX:.0f} ha"], fontsize=6)
        ins.set_xticks([])
        for sp in ("top", "right", "bottom"):
            ins.spines[sp].set_visible(False)
        ins.tick_params(length=0)
        ins.patch.set_alpha(0.75)
    # The directory is re-asserted per frame, not once at the start. A 229-month
    # render is a twenty-minute job and anything that removes the directory
    # underneath it - a tidy-up, a sync, a session working in the same tree -
    # otherwise loses the whole run at whatever month it had reached.
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"frame_{month:%Y_%m}.png"
    fig.savefig(p, dpi=SERIES_FRAME_DPI, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    return p


def _series_plot(D):
    """The series, both bases, with the imagery months and the floor marked.

    The dry-control months are drawn ON the series rather than quoted beside it,
    because D-164's rule - that an area and its false-positive floor are quoted
    together or not at all - is easier to honour in a figure than in a caption.
    """
    import matplotlib                                        # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                          # noqa: PLC0415

    P = D[D["flooded_ha"].notna()].copy()
    if not len(P):
        return
    P["t"] = pd.to_datetime(P["month"] + "-01")
    fig, (ax, bx) = plt.subplots(2, 1, figsize=(13.5, 7.6), sharex=True,
                                 height_ratios=[3, 1])
    for label, colour, lw in (("all", "#a8c8e4", 1.0),
                              ("panel", SERIES_WATER_COLOUR, 1.4)):
        S = P[P["basis"] == label].sort_values("t")
        if not len(S):
            continue
        ax.plot(S["t"], S["flooded_ha"], color=colour, lw=lw,
                label=("fixed panel" if label == "panel"
                       else "all available (sensitivity)"), zorder=3)
    S = P[P["basis"] == "panel"].sort_values("t")
    if not len(S):
        S = P.sort_values("t")
    dc = S[S["dry_control_month"]]
    im = S[S["imagery_month"] & ~S["dry_control_month"]]
    if len(dc):
        ax.scatter(dc["t"], dc["flooded_ha"], s=34, color="#d95f02",
                   zorder=5, label="dry control (the false-positive floor)")
        ax.axhline(float(dc["flooded_ha"].max()), color="#d95f02", lw=0.8,
                   ls=":", zorder=2)
    if len(im):
        ax.scatter(im["t"], im["flooded_ha"], s=34, facecolor="none",
                   edgecolor="#238b45", lw=1.2, zorder=5,
                   label="imagery month (validated)")
    # THE WEAK SPAN IS MARKED ON THE FIGURE, not truncated out of it (Martin,
    # 2026-09-13). The panel's MEMBERSHIP is fixed from the start but its
    # REPORTING is not: before it is substantially complete the surface rests on
    # 20-30 wells at roughly half again the leave-one-out error. Those months are
    # real and are shown; they are simply not comparable with the rest, and the
    # figure says so where a reader cannot miss it.
    W = S[S["panel_frac"] < SERIES_PANEL_COMPLETE_FRAC] if "panel_frac" in S \
        else S.iloc[0:0]
    if len(W):
        lo, hi = W["t"].min(), W["t"].max()
        for a_ in (ax, bx):
            a_.axvspan(lo, hi, color="#fee6ce", alpha=0.75, lw=0, zorder=0)
        ax.axvline(hi, color="#e6550d", lw=0.9, ls="--", zorder=2)
        ax.text(lo, ax.get_ylim()[1] * 0.97,
                f"  reduced network — {int(W['n_wells'].median())} of "
                f"{int(S['n_wells'].max())} wells, LOO "
                f"{W['loo_m'].median():.2f} m\n  indicative only, not "
                f"comparable month to month",
                ha="left", va="top", fontsize=8.5, color="#8c2d04", zorder=6)
    ax.set_ylabel("flooded area (ha)")
    ax.legend(frameon=False, fontsize=9, ncol=2, loc="upper right")
    ax.set_title("Newborough Warren — modelled flooded area, monthly. "
                 "Every area is net of nothing.", loc="left")
    bx.fill_between(S["t"], 0, S["n_wells"], color="#999999", alpha=0.5, lw=0)
    bx.set_ylabel("wells")
    bx.set_xlabel("")
    for a_ in (ax, bx):
        for sp in ("top", "right"):
            a_.spines[sp].set_visible(False)
    fig.tight_layout()
    q = OUT / "W94_51_flood_series.png"
    fig.savefig(q, dpi=150, facecolor="white")
    plt.close(fig)
    saved(q.name)


def phase14(frames=False, basis="both", months=0) -> int:
    """The monthly flooded-area series, 2005-2026.

    Phase 13 run over every month in the record instead of the eight imagery
    dates. Nothing about the method changes: PHASE9_DEM_BIAS_M, z_b, the lake
    gauge excluded, the estuary boundary condition, floors from merge-tree slack
    units - all as D-164 and D-165 settled them.

    TWO SERIES, AND THE PAIR IS THE POINT (Martin, 2026-09-13). The headline is
    a FIXED PANEL, because the network trebles across the record and a series on
    all available wells cannot separate a rising water table from a growing
    dipwell network (see `_series_panel`). The all-available series is computed
    alongside, over the longer span, and the two are plotted together so the
    density effect is visible where they overlap rather than argued about.

    WHAT THIS SERIES IS NOT. It is MODELLED: eight of its months are validated
    against the imagery read, the rest are interpolation between wells, and the
    leave-one-out error is carried on every row so no figure can be quoted
    without it. EVERY AREA IS NET OF NOTHING - the dry-control false-positive
    floor is not subtracted, because D-164 records that it is not known to be
    uniform across dates. The four dry controls are themselves months of this
    series, so the floor is legible INSIDE it rather than being a footnote.
    And producing the series is not fitting a trend to it: that is a separate
    job with its own attribution question.
    """
    import contextlib                                          # noqa: PLC0415
    import io                                                   # noqa: PLC0415

    from utils.warren_mask import (closure_dates,               # noqa: PLC0415
                                   warren_on)
    phase(14, "The monthly flooded-area series")
    # The canopy table is printed by closure_dates and is the same every month.
    # Resolve it ONCE and pass it in, or 229 months print it 229 times and the
    # run's own findings are lost in it.
    closures = closure_dates()

    zb = ESTUARY_LEVEL_M_AOD
    wells = pd.read_csv(REPO / "outputs" / "01_well_elevations.csv",
                        float_precision="round_trip")
    lev = _level_frame()
    ground = {str(n).lower(): float(g) for n, g
              in zip(wells["Name"], wells["ground_elev_m"])}
    en = {str(n).lower(): (float(e), float(nn)) for n, e, nn
          in zip(wells["Name"], wells["E"], wells["N"])}

    panel, every = _series_panel(lev, ground)
    step(f"fixed panel: {len(panel)} well(s) with >= "
         f"{SERIES_PANEL_MIN_COVERAGE:.0%} coverage from {SERIES_PANEL_START}; "
         f"all-available: {len(every)} well(s)")

    runs = []
    if basis in ("both", "panel"):
        runs.append(("panel", panel, pd.Timestamp(SERIES_PANEL_START)))
    if basis in ("both", "all"):
        runs.append(("all", every, None))

    mon = pd.to_datetime(lev["month"])
    cache = {}
    frame_dir = OUT / "W94_frames"
    if frames:
        frame_dir.mkdir(exist_ok=True)

    rows = []
    for label, names, start in runs:
        sel = mon if start is None else mon[mon >= start]
        if months:
            sel = sel.iloc[:months]
        step(f"{label}: {len(sel)} month(s)")
        for month in sel:
            row = lev.loc[mon == month].iloc[0]
            xs, ys, wt = [], [], []
            for c in names:
                v = pd.to_numeric(pd.Series([row[c]]), errors="coerce").iloc[0]
                if pd.isna(v):
                    continue
                k = str(c).lower()
                xs.append(en[k][0])
                ys.append(en[k][1])
                wt.append(ground[k] + float(v))
            if len(xs) < MIN_WELLS_FOR_SURFACE:
                rows.append({"basis": label, "month": f"{month:%Y-%m}",
                             "n_wells": len(xs), "flooded_ha": None,
                             "units_flooded": None, "median_depth_m": None,
                             "loo_m": None, "wet_wells": None,
                             "panel_frac": (round(len(xs) / len(names), 3)
                                            if names else None),
                             "warren_ha": None, "imagery_month": False,
                             "dry_control_month": False})
                continue
            with contextlib.redirect_stdout(io.StringIO()):
                site = warren_on(f"{month:%Y-%m-15}", closures=closures)
            arr, unit, ok, tr, res = _units_for(site, cache)
            rows_, cols_ = np.nonzero(ok)
            EE, NN = rasterio.transform.xy(tr, rows_, cols_)
            EE = np.asarray(EE)
            NN = np.asarray(NN)
            Z = arr[ok]
            cell_ha = res * res / 1e4

            BE, BN = _estuary_control(site)
            X = np.concatenate([xs, BE]) if len(BE) else np.asarray(xs)
            Y = np.concatenate([ys, BN]) if len(BE) else np.asarray(ys)
            V = (np.concatenate([wt, np.full(len(BE), zb)]) if len(BE)
                 else np.asarray(wt))
            surf = _idw(X, Y, V, EE, NN)
            wet = Z < surf
            dep = (surf - Z)[wet]
            area = float(wet.sum()) * cell_ha

            # Leave-one-out at the wells, on THIS month's panel: the honest
            # statement of how much the interpolation between them matters.
            ax_, ay_, av_ = np.asarray(xs), np.asarray(ys), np.asarray(wt)
            loo = []
            for i in range(len(ax_)):
                m_ = np.ones(len(ax_), bool)
                m_[i] = False
                d_ = np.hypot(ax_[m_] - ax_[i], ay_[m_] - ay_[i]) + 1e-6
                w_ = 1.0 / d_ ** 2
                loo.append((w_ * av_[m_]).sum() / w_.sum() - av_[i])
            rows.append({
                "basis": label, "month": f"{month:%Y-%m}", "n_wells": len(xs),
                "flooded_ha": round(area, 3),
                "units_flooded": int(len(np.unique(unit[ok][wet]))),
                "median_depth_m": (round(float(np.median(dep)), 3)
                                   if dep.size else None),
                "loo_m": round(float(np.median(np.abs(loo))), 3),
                "wet_wells": int(sum(1 for c in names
                                     if pd.notna(row.get(c))
                                     and float(row[c]) >= 0.0)),
                "panel_frac": (round(len(xs) / len(names), 3)
                               if names else None),
                "warren_ha": round(site.area / 1e4, 2),
                "imagery_month": f"{month:%Y-%m}" in _IMAGERY_MONTHS,
                "dry_control_month": f"{month:%Y-%m}" in _DRY_MONTHS})
            if frames and label == "panel":
                so_far = [r["flooded_ha"] for r in rows
                          if r["basis"] == "panel"
                          and r["flooded_ha"] is not None]
                _series_frame(month, EE, NN, ok, wet, dep, area, len(xs),
                              site, frame_dir, so_far=so_far,
                              weak=(len(xs) / len(names)
                                    < SERIES_PANEL_COMPLETE_FRAC),
                              panel_n=len(names))

    D = pd.DataFrame(rows)
    p = OUT / "W94_50_flood_series.csv"
    D.to_csv(p, index=False)
    saved(p.name)

    for label in D["basis"].unique():
        S = D[(D["basis"] == label) & D["flooded_ha"].notna()]
        if not len(S):
            continue
        info(f"  {label}: {len(S)} month(s) computed, "
             f"{int((D['basis'] == label).sum()) - len(S)} skipped for too few "
             f"wells; area {S['flooded_ha'].min():.2f}-"
             f"{S['flooded_ha'].max():.2f} ha, median "
             f"{S['flooded_ha'].median():.2f}; LOO median "
             f"{S['loo_m'].median():.3f} m")
        if label == "panel" and "panel_frac" in S:
            full = S[S["panel_frac"] >= SERIES_PANEL_COMPLETE_FRAC]
            if len(full):
                info(f"    the panel is >= "
                     f"{SERIES_PANEL_COMPLETE_FRAC:.0%} complete from "
                     f"{full['month'].min()}; before that it reports "
                     f"{int(S[S['panel_frac'] < SERIES_PANEL_COMPLETE_FRAC]['n_wells'].median())} "
                     f"well(s) at a median LOO of "
                     f"{S[S['panel_frac'] < SERIES_PANEL_COMPLETE_FRAC]['loo_m'].median():.3f} m "
                     f"against {full['loo_m'].median():.3f} m after — MEMBERSHIP "
                     f"is fixed from the start, REPORTING is not, and only the "
                     f"complete span is comparable month to month")
        dc = S[S["dry_control_month"]]
        if len(dc):
            info(f"    the dry-control months sit at "
                 f"{dc['flooded_ha'].min():.2f}-{dc['flooded_ha'].max():.2f} ha "
                 f"— the false-positive floor, INSIDE the series")
    _series_plot(D)
    if frames:
        n = len(list(frame_dir.glob("frame_*.png")))
        step(f"{n} frame(s) in {frame_dir.name}/ — build the animation with "
             f"tools/make_flood_animation.sh")
    info("EVERY AREA IS NET OF NOTHING and the series is MODELLED: eight "
         "months are validated against the imagery read, the rest are "
         "interpolation. Quote the area, the floor and the basis together.")
    return 0

def phase15(depths=None) -> int:
    """Is SLACK_MIN_DEPTH_M defensible against the imagery? A sweep.

    THE QUESTION. Only 28.8 % of the water the imagery reads on 2021-03-24 lies
    inside a merge-tree slack unit at all (22.81 of 79.15 ha); the phase 6
    hollows contain 58.2 %. So the unit definition, not the water table, sets
    most of the gap between the model and the photograph — and the constant
    doing the excluding is SLACK_MIN_DEPTH_M, which has never been tested against
    this evidence. Martin, 2026-09-13: *"test the slack depth against the
    imagery"*.

    WHAT IS SWEPT AND WHAT IS NOT. Only the selection off the merge tree. The
    tree itself does not depend on the threshold, so nothing is rebuilt and no
    other constant moves: the bias, z_b, the estuary boundary, the level frame
    and SLACK_MIN_AREA_M2 are all held.

    THE FALSIFICATION CRITERIA, stated before the run:

      1. A lower threshold that raises the DRY CONTROLS as fast as it raises the
         wet dates has bought nothing — it is admitting noise, not slacks. The
         test is the MARGIN, wettest over the worst dry control, which must not
         fall below DRY_CONTROL_MIN_RATIO.
      2. A threshold whose reachable fraction rises while the margin holds is a
         real improvement, and the size of the improvement is the size of the
         case for changing the constant.
      3. If the margin falls monotonically as the threshold falls, the committed
         0.10 m is doing exactly what it was put there to do and the 29 % is a
         property of the ground rather than of the constant. That is a NO, and
         it is as useful an answer as a yes.

    NOTHING IS WRITTEN TO config.py BY THIS PHASE. It reports a curve. Changing
    SLACK_MIN_DEPTH_M moves every slack floor, the extent series and D-164's dry
    controls together, so it belongs in a D-entry.
    """
    from utils.warren_mask import warren_on                     # noqa: PLC0415
    from utils.config import SLACK_MIN_DEPTH_M                  # noqa: PLC0415
    phase(15, "SLACK_MIN_DEPTH_M against the imagery")

    ds_ = sorted(set(list(DRY_CALIBRATION_DATES)
                     + ["2021-03-24", "2021-04-04", "2020-03-31", "2017-03-24"]))
    sweep = ([float(x) for x in depths] if depths
             else [0.02, 0.04, 0.06, 0.08, 0.10, 0.15, 0.20, 0.30])
    if SLACK_MIN_DEPTH_M not in sweep:
        sweep = sorted(set(sweep + [SLACK_MIN_DEPTH_M]))

    zb = ESTUARY_LEVEL_M_AOD
    wells = pd.read_csv(REPO / "outputs" / "01_well_elevations.csv",
                        float_precision="round_trip")
    lev = _level_frame()
    ground = {str(n).lower(): float(g) for n, g
              in zip(wells["Name"], wells["ground_elev_m"])}

    site = warren_on(max(ds_))
    BE, BN = _estuary_control(site)

    # The imagery water this date, for the reachable-fraction measurement. The
    # vp2 read is the one with three dates; the tile read is one date and is
    # reported beside it where it exists.
    reads = {}
    for f in sorted(OUT.glob("W94_08_flood_*.geojson")):
        tag = "tiles" if "_tiles_" in f.name else "vp2"
        d = f.stem.split("flood_")[1].replace("tiles_", "")
        reads[(tag, d)] = gpd.read_file(f).set_crs(OSGB, allow_override=True)
    step(f"{len(reads)} imagery read(s) for the reachable fraction: "
         f"{', '.join(sorted({k[1] for k in reads}))}")

    rows = []
    for depth in sweep:
        arr, unit, ok, tr, res = _slack_units(site, PHASE9_DEM_BIAS_M,
                                              depth_m=depth, quiet=True)
        rows_, cols_ = np.nonzero(ok)
        EE, NN = rasterio.transform.xy(tr, rows_, cols_)
        EE = np.asarray(EE)
        NN = np.asarray(NN)
        Z = arr[ok]
        cell_ha = res * res / 1e4
        ceiling = float(ok.sum()) * cell_ha

        # how much of each imagery read this unit set can reach
        reach = {}
        pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(EE, NN), crs=OSGB)
        for (tag, d), g in reads.items():
            tot = float(g.area.sum()) / 1e4
            inside = gpd.sjoin(pts, g[["geometry"]], how="inner",
                               predicate="within")
            reach[(tag, d)] = (len(inside) * cell_ha, tot)

        for d in ds_:
            wl = _well_levels(lev, wells, d)
            if wl is None or not len(wl):
                continue
            xs, ys, wt = [], [], []
            for _, r in wl.iterrows():
                k = str(r["well"]).lower()
                if k in ground and k != LAKE_GAUGE_NAME:
                    xs.append(float(r["E"]))
                    ys.append(float(r["N"]))
                    wt.append(ground[k] + float(r["h_m"]))
            if len(xs) < MIN_WELLS_FOR_SURFACE:
                continue
            X = np.concatenate([xs, BE]) if len(BE) else np.asarray(xs)
            Y = np.concatenate([ys, BN]) if len(BE) else np.asarray(ys)
            V = (np.concatenate([wt, np.full(len(BE), zb)]) if len(BE)
                 else np.asarray(wt))
            wet = Z < _idw(X, Y, V, EE, NN)
            rch = reach.get(("vp2", d)) or reach.get(("tiles", d))
            rows.append({
                "slack_min_depth_m": depth, "date": d,
                "ceiling_ha": round(ceiling, 3),
                "flooded_ha": round(float(wet.sum()) * cell_ha, 3),
                "dry_control": d in DRY_CALIBRATION_DATES,
                "imagery_ha": round(rch[1], 3) if rch else None,
                "reachable_ha": round(rch[0], 3) if rch else None,
                "reachable_frac": (round(rch[0] / rch[1], 4)
                                   if rch and rch[1] else None),
                "committed": depth == SLACK_MIN_DEPTH_M})
        S = pd.DataFrame([r for r in rows
                          if r["slack_min_depth_m"] == depth])
        dry = S[S["dry_control"]]["flooded_ha"].max()
        wetm = S[~S["dry_control"]]["flooded_ha"].max()
        rr = S["reachable_frac"].dropna()
        info(f"  depth {depth:.2f} m  ceiling {ceiling:6.1f} ha  "
             f"reachable {rr.max() * 100 if len(rr) else float('nan'):5.1f}%  "
             f"dry max {dry:6.2f}  wettest {wetm:6.2f}  "
             f"margin {wetm / dry if dry else float('nan'):5.2f}:1"
             + ("   [COMMITTED]" if depth == SLACK_MIN_DEPTH_M else ""))

    D = pd.DataFrame(rows)
    p = OUT / "W94_60_slack_depth_sweep.csv"
    D.to_csv(p, index=False)
    saved(p.name)

    g = D.groupby("slack_min_depth_m")
    summ = pd.DataFrame({
        "ceiling_ha": g["ceiling_ha"].first(),
        "reachable_frac": g["reachable_frac"].max(),
        "dry_max_ha": g.apply(lambda x: x[x.dry_control]["flooded_ha"].max(),
                              include_groups=False),
        "wettest_ha": g.apply(lambda x: x[~x.dry_control]["flooded_ha"].max(),
                              include_groups=False)})
    summ["margin"] = summ["wettest_ha"] / summ["dry_max_ha"]
    q = OUT / "W94_61_slack_depth_summary.csv"
    summ.round(4).to_csv(q)
    saved(q.name)

    best = summ[summ["margin"] >= DRY_CONTROL_MIN_RATIO]
    if len(best):
        pick = best["reachable_frac"].idxmax()
        step(f"the deepest reach with the margin still above "
             f"{DRY_CONTROL_MIN_RATIO}:1 is depth {pick:.2f} m — "
             f"{summ.loc[pick, 'reachable_frac'] * 100:.1f}% of the imagery "
             f"reachable at margin {summ.loc[pick, 'margin']:.2f}:1, against "
             f"{summ.loc[SLACK_MIN_DEPTH_M, 'reachable_frac'] * 100:.1f}% and "
             f"{summ.loc[SLACK_MIN_DEPTH_M, 'margin']:.2f}:1 committed")
    else:
        warn("  NO depth in the sweep holds the margin — the committed value "
             "stands and the 29 % is a property of the ground")
    info("NOTHING IS WRITTEN TO config.py. Changing SLACK_MIN_DEPTH_M moves "
         "every slack floor, the extent series and D-164's dry controls "
         "together; it belongs in a D-entry, not in a tool.")
    return 0

def phase16(date="2021-03-24", series="tiles") -> int:
    """Why the modelled surface does not reach the floors the imagery says are wet.

    THE QUESTION THIS SETTLES. Decomposing the 2021-03-24 tile read cell by cell,
    34.5 % of the observed water (30.4 of 88.2 ha) lies inside a properly mapped
    slack unit whose floor the modelled water table never reaches. That is larger
    than the area filter's effect and it is not about what counts as a slack: the
    surface is simply too low. Martin, 2026-09-13. This measures the shortfall
    per slack and asks what it is a function of.

    THE DISCRIMINATION, stated before the run, because a shortfall that is one
    thing looks like a shortfall that is another:

      * **A UNIFORM OFFSET** - tight spread, no structure against distance to the
        nearest well or to the estuary boundary - means a CONSTANT is wrong, and
        the median shortfall is itself the size of the correction. PHASE9_DEM_BIAS_M
        and z_b are the two candidates.
      * **STRUCTURE AGAINST DISTANCE TO THE NEAREST WELL** means the interpolation
        cannot resolve the water table between wells, which is a method limit to
        be stated, not a constant to be tuned.
      * **STRUCTURE AGAINST DISTANCE TO THE ESTUARY** means the boundary condition
        is dragging the surface down, and z_b or the boundary's reach is the lever.
      * **NO STRUCTURE AND A WIDE SPREAD** means the slack floors themselves are
        wrong per slack, which sends the question back to the DEM.

    The four are not exclusive and the point of measuring is to say which
    dominates rather than to pick one.

    NOTHING IS WRITTEN TO config.py. This reports a diagnosis.
    """
    from utils.warren_mask import warren_on                     # noqa: PLC0415
    from rasterio.features import geometry_mask                 # noqa: PLC0415
    phase(16, "The per-slack shortfall — why the surface misses the floors")

    zb = ESTUARY_LEVEL_M_AOD
    wells = pd.read_csv(REPO / "outputs" / "01_well_elevations.csv",
                        float_precision="round_trip")
    lev = _level_frame()
    ground = {str(n).lower(): float(g) for n, g
              in zip(wells["Name"], wells["ground_elev_m"])}

    site = warren_on(date)
    arr, unit, ok, tr, res = _slack_units(site, PHASE9_DEM_BIAS_M)
    cell_ha = res * res / 1e4

    tag = "tiles_" if series == "tiles" else ""
    p = OUT / f"W94_08_flood_{tag}{date}.geojson"
    if not p.exists():
        warn(f"no {series} read for {date}: {p.name} is missing")
        return 1
    g = gpd.read_file(p).set_crs(OSGB, allow_override=True)
    water = geometry_mask(list(g.geometry), out_shape=arr.shape,
                          transform=tr, invert=True)
    info(f"{series} read: {g.area.sum() / 1e4:.1f} ha over {len(g)} polygon(s)")

    # the modelled surface, on every cell of every unit
    BE, BN = _estuary_control(site)
    wl = _well_levels(lev, wells, date)
    xs, ys, wt = [], [], []
    for _, r in wl.iterrows():
        k = str(r["well"]).lower()
        if k in ground and k != LAKE_GAUGE_NAME:
            xs.append(float(r["E"]))
            ys.append(float(r["N"]))
            wt.append(ground[k] + float(r["h_m"]))
    step(f"{len(xs)} well(s) on {date}; "
         f"{int((wl['h_m'] >= 0).sum())} at or above ground")
    rows_, cols_ = np.nonzero(ok)
    EE, NN = rasterio.transform.xy(tr, rows_, cols_)
    EE = np.asarray(EE)
    NN = np.asarray(NN)
    X = np.concatenate([xs, BE]) if len(BE) else np.asarray(xs)
    Y = np.concatenate([ys, BN]) if len(BE) else np.asarray(ys)
    V = (np.concatenate([wt, np.full(len(BE), zb)]) if len(BE)
         else np.asarray(wt))
    surf = _idw(X, Y, V, EE, NN)
    Z = arr[ok]
    uid = unit[ok]
    wetobs = water[rows_, cols_]

    WX, WY = np.asarray(xs), np.asarray(ys)
    out = []
    for u in np.unique(uid):
        m = uid == u
        n_cell = int(m.sum())
        obs_frac = float(wetobs[m].mean())
        if obs_frac < SHORTFALL_MIN_WET_FRAC:
            continue
        floor = float(Z[m].min())
        # the surface over this slack, at its own cells
        s_here = float(np.median(surf[m]))
        ex, ey = float(EE[m].mean()), float(NN[m].mean())
        dw = float(np.min(np.hypot(WX - ex, WY - ey))) if len(WX) else np.nan
        de = (float(np.min(np.hypot(BE - ex, BN - ey)))
              if len(BE) else np.nan)
        out.append({"unit": int(u), "cells": n_cell,
                    "area_ha": round(n_cell * cell_ha, 4),
                    "obs_wet_frac": round(obs_frac, 3),
                    "floor_m_aod": round(floor, 3),
                    "surface_m_aod": round(s_here, 3),
                    "shortfall_m": round(floor - s_here, 3),
                    "modelled_flooded": bool(s_here > floor),
                    "E": round(ex, 1), "N": round(ey, 1),
                    "dist_well_m": round(dw, 1),
                    "dist_estuary_m": round(de, 1)})
    if not out:
        warn("no slack unit is observed wet; nothing to diagnose")
        return 1
    D = pd.DataFrame(out)
    q = OUT / f"W94_70_slack_shortfall_{date}.csv"
    D.to_csv(q, index=False)
    saved(q.name)

    miss = D[~D["modelled_flooded"]]
    step(f"{len(D)} slack unit(s) observed wet at >= "
         f"{SHORTFALL_MIN_WET_FRAC:.0%} of their cells; the model floods "
         f"{int(D['modelled_flooded'].sum())} and misses {len(miss)} "
         f"({len(miss) / len(D) * 100:.0f}%)")
    sf = miss["shortfall_m"]
    if len(sf):
        info(f"  shortfall on the missed slacks: median {sf.median():+.3f} m, "
             f"IQR {sf.quantile(.25):+.3f} to {sf.quantile(.75):+.3f}, "
             f"p90 {sf.quantile(.90):+.3f}")
        for lab, col in (("distance to the nearest well", "dist_well_m"),
                         ("distance to the estuary boundary",
                          "dist_estuary_m"),
                         ("slack area", "area_ha"),
                         ("floor elevation", "floor_m_aod")):
            r_ = miss[["shortfall_m", col]].corr().iloc[0, 1]
            info(f"  shortfall vs {lab:34s} r = {r_:+.3f}")
        iqr = float(sf.quantile(.75) - sf.quantile(.25))
        step("READING IT: a tight spread with no structure is a CONSTANT; "
             "structure against well distance is an interpolation limit; "
             "structure against the estuary is the boundary condition.")
        info(f"  the IQR of the shortfall is {iqr:.3f} m against a median of "
             f"{sf.median():.3f} m — "
             + ("TIGHT, which points at a constant"
                if iqr < abs(sf.median()) else
                "WIDE relative to the median, which does not"))
    _shortfall_plot(D, date)
    info("NOTHING IS WRITTEN TO config.py. This reports a diagnosis; the "
         "correction it implies is a decision.")
    return 0


def _shortfall_plot(D, date):
    """Four panels, because four explanations have to be told apart."""
    import matplotlib                                          # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                            # noqa: PLC0415

    miss = D[~D["modelled_flooded"]]
    fig, ax = plt.subplots(2, 2, figsize=(13, 9.5))
    a = ax[0][0]
    a.hist(D["shortfall_m"], bins=40, color="#9ecae1", edgecolor="#3182bd")
    a.axvline(0, color="#333333", lw=1)
    if len(miss):
        a.axvline(miss["shortfall_m"].median(), color="#d95f02", lw=1.4,
                  ls="--", label=f"median miss {miss['shortfall_m'].median():+.3f} m")
        a.legend(frameon=False, fontsize=9)
    a.set_xlabel("floor − modelled surface (m);  positive = model says dry")
    a.set_ylabel("slack units")
    a.set_title("How far short, and is it one number?", loc="left")
    for a_, col, lab in ((ax[0][1], "dist_well_m", "distance to nearest well (m)"),
                         (ax[1][0], "dist_estuary_m",
                          "distance to estuary boundary (m)")):
        a_.scatter(D[col], D["shortfall_m"], s=10, alpha=0.5,
                   color=SERIES_WATER_COLOUR)
        a_.axhline(0, color="#333333", lw=1)
        a_.set_xlabel(lab)
        a_.set_ylabel("shortfall (m)")
        if len(miss):
            r_ = miss[["shortfall_m", col]].corr().iloc[0, 1]
            a_.set_title(f"r = {r_:+.3f} on the missed slacks", loc="left")
    a = ax[1][1]
    sc = a.scatter(D["E"], D["N"], c=D["shortfall_m"], s=12, cmap="RdBu_r",
                   vmin=-1, vmax=1)
    a.set_aspect("equal")
    a.set_xlabel("Easting (m)")
    a.set_ylabel("Northing (m)")
    a.set_title("where the shortfall is — red = model too dry", loc="left")
    fig.colorbar(sc, ax=a, shrink=0.8, label="shortfall (m)")
    fig.suptitle(f"Newborough Warren {date} — slack units the imagery says are "
                 f"wet, against the modelled water table", x=0.02, ha="left")
    fig.tight_layout()
    p = OUT / f"W94_71_slack_shortfall_{date}.png"
    fig.savefig(p, dpi=140, facecolor="white")
    plt.close(fig)
    saved(p.name)

def _hollow_predictors():
    """The hollows, with the place-properties the fit reasons about.

    EWI is the one that carries the SSM. Script 26's Equilibrium Wetness Index is
    the steady-state spring level each well's OWN coefficients imply under
    long-term mean climate - a property of the place, not of the month - so
    interpolating it to each hollow is how the cluster SSM behaviour enters a
    model of WHERE flooding occurs. Everything else is geometry the hollows layer
    already carries.
    """
    H = gpd.read_file(OUT / "W94_06_hollows.geojson").set_crs(OSGB,
                                                              allow_override=True)
    E = pd.read_csv(REPO / "outputs" / "26_van_willegen_msl"
                    / "26_equilibrium_wetness_index_per_well.csv",
                    float_precision="round_trip")
    E = E.dropna(subset=["EWI_m_bg", "E", "N"])
    cen = H.geometry.centroid
    H["cx"] = cen.x
    H["cy"] = cen.y
    H["ewi_m_bg"] = _idw(E["E"].to_numpy(), E["N"].to_numpy(),
                         E["EWI_m_bg"].to_numpy(), H["cx"].to_numpy(),
                         H["cy"].to_numpy())
    H["log_area"] = np.log10(H["area_ha"].clip(lower=1e-4))
    keep = ["id", "area_ha", "log_area", "floor_m", "depth_m",
            "nearest_well_m", "ewi_m_bg", "cx", "cy", "geometry"]
    H = H[[c for c in keep if c in H.columns]].copy()
    info(f"{len(H)} hollow(s); EWI interpolated from {len(E)} well(s), "
         f"range {H['ewi_m_bg'].min():+.2f} to {H['ewi_m_bg'].max():+.2f} m "
         f"below ground")
    return H


def _wet_fraction(H, path):
    """Each hollow's share of area the read maps as water."""
    g = gpd.read_file(path).set_crs(OSGB, allow_override=True)
    u = g.geometry.union_all()
    out = []
    for geom, a in zip(H.geometry, H["area_ha"]):
        try:
            out.append(min(1.0, (geom.intersection(u).area / 1e4) / a)
                       if a > 0 else 0.0)
        except Exception:                                     # noqa: BLE001
            out.append(0.0)
    return np.asarray(out, float)


def _site_index(lev, wells):
    """The measured wetness of the site, month by month.

    The fraction of REPORTING dipwells standing at or above ground. It is a
    measurement, it exists for every month of the record, and the whole-warren
    SSM's only job in this model is to reproduce it where there are no dipwells
    to measure - which is why it, and not the SSM, is the training predictor.
    """
    ground = {str(n).lower() for n in wells["Name"]}
    cols = [c for c in lev.columns
            if c != "month" and str(c).lower() in ground
            and str(c).lower() != LAKE_GAUGE_NAME]
    V = lev[cols].apply(pd.to_numeric, errors="coerce")
    n = V.notna().sum(axis=1)
    frac = (V >= 0).sum(axis=1) / n.replace(0, np.nan)
    return pd.DataFrame({"month": pd.to_datetime(lev["month"]),
                         "n_wells": n, "wet_well_frac": frac})


def phase17(min_wells=20) -> int:
    """Flooding regressed on wetness, per hollow, trained on the imagery.

    THE ORDER IS INVERTED, and that is the point. Phases 12-14 interpolate a
    water table, difference it against DEM floors, and only then meet an
    observation - two error sources compounding before anything is checked.
    Phase 16 measured the first (714 of 1,236 observed-wet slacks missed by a
    median of 1.278 m, structured on distance to the nearest well) and --form
    depth the second. THIS asks the imagery which hollows flood under which site
    conditions and fits that directly. No surface, no floors, and no
    PHASE9_DEM_BIAS_M, SLACK_MIN_DEPTH_M or SLACK_MIN_AREA_M2 anywhere in it.

    THE UNIT IS THE HOLLOW, NOT THE DATE. 1,078 hollows on each read date, with
    the hollow's WET FRACTION as the response, so the thinness of the date list
    limits how much the fit can learn about TIME, not about PLACE.

    TWO READS, NEVER AVERAGED. Panel A (tiles, 1.00 m/px) and panel B (vp2,
    2.884 m/px) agree on 69.38 ha of 2021-03-24 - 78.6 % of A, 87.7 % of B - so
    the disagreement is a margin at the edges of a shared core. Both are fitted
    and every prediction is the pair. AN ASYMMETRY TO STATE: the tile read exists
    for ONE date, so fit A is fit B with 2021-03-24 swapped for the tile read,
    and the difference between them is the read uncertainty on the one date they
    share - not two independent models.

    WHAT IT IS NOT. Not a physical model, and it must never be called one; it is
    a calibrated empirical relationship. It predicts flooding IN MAPPED HOLLOWS,
    and phase 16 put 37.7 % of the 2021-03-24 water outside any closed basin, so
    its totals are slack flooding and are stated as such.
    """
    import statsmodels.api as sm                              # noqa: PLC0415
    phase(17, "Flooding regressed on wetness, per hollow")

    H = _hollow_predictors()
    wells = pd.read_csv(REPO / "outputs" / "01_well_elevations.csv",
                        float_precision="round_trip")
    lev = _level_frame()
    SI = _site_index(lev, wells)

    reads = {}
    for f in sorted(OUT.glob("W94_08_flood_*.geojson")):
        tag = "A_tiles" if "_tiles_" in f.name else "B_vp2"
        d = f.stem.split("flood_")[1].replace("tiles_", "")
        reads[(tag, d)] = f
    dry = [(d, None) for d in DRY_CALIBRATION_DATES]
    step(f"reads: {', '.join(f'{t.split(chr(95))[0]} {d}' for t, d in reads)}"
         f"  |  dry controls as zeros: {', '.join(d for d, _ in dry)}")

    rows = []
    for (tag, d), f in reads.items():
        wf = _wet_fraction(H, f)
        rows.append(pd.DataFrame({"read": tag, "date": d, "id": H["id"],
                                  "wet_frac": wf}))
        info(f"  {tag} {d}: hollow-weighted water "
             f"{float((wf * H['area_ha']).sum()):.2f} ha over "
             f"{int((wf > 0).sum())} hollow(s)")
    for d, _ in dry:
        for tag in sorted({t for t, _ in reads}):
            rows.append(pd.DataFrame({"read": tag, "date": d, "id": H["id"],
                                      "wet_frac": 0.0}))
    T = pd.concat(rows, ignore_index=True)
    T = T.merge(H.drop(columns="geometry"), on="id", how="left")
    T["month"] = pd.to_datetime(T["date"]).dt.to_period("M").dt.to_timestamp()
    T = T.merge(SI, on="month", how="left")
    T["is_dry_control"] = T["date"].isin(DRY_CALIBRATION_DATES)
    T["cells"] = (T["area_ha"] * 1e4 / 4.0).clip(lower=1.0)
    p = OUT / "W94_80_training_table.csv"
    T.to_csv(p, index=False)
    saved(f"{p.name}  ({len(T)} row(s))")

    PRED = ["wet_well_frac", "ewi_m_bg", "depth_m", "log_area", "floor_m",
            "nearest_well_m"]
    fits, coefs = {}, []
    # Fit A is fit B with the shared date's read swapped, not an independent
    # model: the tile read covers one date.
    base = T[T["read"] == "B_vp2"]
    swap = T[(T["read"] == "A_tiles")]
    setA = pd.concat([base[~base["date"].isin(swap["date"])], swap],
                     ignore_index=True)
    for name, D in (("B_vp2", base), ("A_tiles", setA)):
        D = D.dropna(subset=PRED + ["wet_frac"])
        X = sm.add_constant(D[PRED].astype(float))
        m = sm.GLM(D["wet_frac"].astype(float), X,
                   family=sm.families.Binomial(),
                   freq_weights=D["cells"].astype(float)).fit()
        fits[name] = (m, D)
        for k in m.params.index:
            coefs.append({"fit": name, "term": k,
                          "coef": round(float(m.params[k]), 5),
                          "se": round(float(m.bse[k]), 5),
                          "z": round(float(m.tvalues[k]), 2),
                          "p": float(m.pvalues[k])})
        step(f"{name}: {len(D)} row(s) over {D['date'].nunique()} date(s); "
             f"pseudo-R2 "
             f"{1 - m.deviance / m.null_deviance:.3f}")
        for k in PRED:
            info(f"    {k:16s} {m.params[k]:+9.4f}  z {m.tvalues[k]:+7.1f}")
    pd.DataFrame(coefs).to_csv(OUT / "W94_81_model_fits.csv", index=False)
    saved("W94_81_model_fits.csv")

    # LEAVE ONE DATE OUT, because hollows within a date share that day's wetness
    loo = []
    for name, (_, D) in fits.items():
        for d in sorted(D["date"].unique()):
            tr_, te = D[D["date"] != d], D[D["date"] == d]
            if tr_["date"].nunique() < 2 or not len(te):
                continue
            mm = sm.GLM(tr_["wet_frac"].astype(float),
                        sm.add_constant(tr_[PRED].astype(float)),
                        family=sm.families.Binomial(),
                        freq_weights=tr_["cells"].astype(float)).fit()
            pr = mm.predict(sm.add_constant(te[PRED].astype(float),
                                            has_constant="add"))
            loo.append({"fit": name, "date": d,
                        "observed_ha": round(float((te["wet_frac"]
                                                    * te["area_ha"]).sum()), 3),
                        "predicted_ha": round(float((pr * te["area_ha"]).sum()),
                                              3),
                        "dry_control": bool(te["is_dry_control"].iloc[0])})
    L = pd.DataFrame(loo)
    L.to_csv(OUT / "W94_82_loo_by_date.csv", index=False)
    saved("W94_82_loo_by_date.csv")
    if len(L):
        step("LEAVE-ONE-DATE-OUT — the only validation that means anything here")
        for r in L.itertuples():
            info(f"    {r.fit:8s} {r.date}  observed {r.observed_ha:7.2f} ha  "
                 f"predicted {r.predicted_ha:7.2f} ha"
                 + ("   [DRY CONTROL]" if r.dry_control else ""))

    # the monthly series, on the MEASURED index, both fits
    S = SI[SI["n_wells"] >= min_wells].copy()
    out = []
    for name, (m, _) in fits.items():
        for r in S.itertuples():
            G = H.drop(columns="geometry").copy()
            G["wet_well_frac"] = r.wet_well_frac
            pr = m.predict(sm.add_constant(G[PRED].astype(float),
                                           has_constant="add"))
            out.append({"fit": name, "month": f"{r.month:%Y-%m}",
                        "n_wells": int(r.n_wells),
                        "wet_well_frac": round(float(r.wet_well_frac), 4),
                        "flooded_ha": round(float((pr * G["area_ha"]).sum()), 3)})
    P = pd.DataFrame(out)
    P.to_csv(OUT / "W94_83_predicted_area.csv", index=False)
    saved(f"W94_83_predicted_area.csv  ({P['month'].nunique()} month(s))")
    w = P.pivot(index="month", columns="fit", values="flooded_ha")
    if {"A_tiles", "B_vp2"} <= set(w.columns):
        band = (w["A_tiles"] - w["B_vp2"]).abs()
        step(f"the A-against-B band is {band.median():.2f} ha at the median and "
             f"{band.max():.2f} ha at its widest — that is the read "
             f"disagreement, carried rather than averaged away")
    info("NOT A PHYSICAL MODEL: a calibrated empirical relationship trained on "
         "a handful of imagery dates, predicting flooding IN MAPPED HOLLOWS "
         "only. Quote it with its band and its training dates.")
    return 0

def _flood_map(date, frame, fg, hollows, sc, thr, tag=""):
    """The read, on the ground: water solid, hollows outlined, wells scored.

    The map is where a false positive stops being a number and becomes a place —
    which is how the CEH32 ridge was found, and how the estuary patch was.
    """
    import matplotlib.pyplot as plt                          # noqa: PLC0415
    from utils.config import (SITE_MAP_EAST_MAX,             # noqa: PLC0415
                              SITE_MAP_EAST_MIN, SITE_MAP_NORTH_MAX,
                              SITE_MAP_NORTH_MIN)
    from utils.map_utils import add_en_axes, load_dem_hillshade  # noqa: PLC0415
    from utils.render_utils import render_figure             # noqa: PLC0415
    from shapely.geometry import Point                       # noqa: PLC0415

    fig, ax = plt.subplots(figsize=(11.5, 9.8))
    load_dem_hillshade(ax, DATA_GEO_DIR, alpha=0.6)
    gpd.GeoSeries([warren_on(date)], crs=OSGB).plot(
        ax=ax, facecolor="none", edgecolor="#08519c", lw=1.0, zorder=3)
    hollows.plot(ax=ax, facecolor="none", edgecolor="#bdd7e7", lw=0.3,
                 zorder=3.5)
    fg.plot(ax=ax, facecolor="#2171b5", edgecolor="#08306b", lw=0.3,
            alpha=0.85, zorder=4)
    per = sc["per_well"]
    if len(per):
        el = pd.read_csv(REPO / "outputs" / "01_well_elevations.csv",
                         float_precision="round_trip")
        en = {str(n).lower(): (x, y) for n, x, y in
              zip(el["Name"], el["E"], el["N"])}
        # FOUR OUTCOMES, four colours. An agreement figure hides WHERE it
        # disagrees, and the where is the evidence.
        style = {(True, True): ("#238b45", "o", "wet, found"),
                 (True, False): ("#cb181d", "v", "wet, missed"),
                 (False, True): ("#fd8d3c", "^", "dry, called wet"),
                 (False, False): ("#737373", ".", "dry, agreed")}
        for key, (col, mk, lab) in style.items():
            sel = per[(per["wet_truth"] == key[0]) & (per["wet_pred"] == key[1])]
            pts = [en.get(str(w).lower()) for w in sel["well"]]
            pts = [q for q in pts if q is not None]
            if not pts:
                continue
            gpd.GeoSeries([Point(*q) for q in pts], crs=OSGB).plot(
                ax=ax, color=col, marker=mk, markersize=26, zorder=5,
                label=f"{lab} ({len(pts)})")
        for _, r in per[per["wet_truth"] != per["wet_pred"]].iterrows():
            q = en.get(str(r["well"]).lower())
            if q:
                ax.annotate(str(r["well"]), q, fontsize=7, xytext=(4, 4),
                            textcoords="offset points", zorder=6)
        ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    ax.set_xlim(SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX)
    ax.set_ylim(SITE_MAP_NORTH_MIN, SITE_MAP_NORTH_MAX)
    add_en_axes(ax, apply_extent=False)
    sm = sc["summary"]
    ax.set_title(
        f"W94 — flood read from {frame}, {date}\n"
        f"{len(fg)} water bod(ies), {fg.area.sum() / 1e4:.1f} ha; "
        # A FIXED CUT MUST NOT BE CAPTIONED AS THE FRAME'S OWN. The two say
        # opposite things about where the threshold came from, and a caption
        # that gets that wrong is how a false-wet map becomes a flood map.
        + (f"cut at a FIXED z = {thr:.2f}, transferred from an accepted wet "
           f"frame, not chosen by this one; " if _fixed_cut else
           f"cut at this frame's own Otsu z = {thr:.2f} against its open dune; ")
        +
        f"recall {sm['recall']}, precision {sm['precision']} "
        f"(a LOWER bound — edge-sited wells) at {sm['n_wells']} wells")
    q = OUT / f"W94_08_flood{tag}_{date}.png"
    render_figure(fig, q)
    saved(q.name)


def _well_levels(lev, wells, date):
    """Wells reporting in the frame's month, with their level.

    BUCKETING IS SCRIPT 01's, not a new convention: a reading on day > 15
    belongs to the same month, day <= 15 to the previous. So 2021-03-24 is
    March 2021, and the frame is compared with the level for the month it
    falls in.
    """
    d = pd.Timestamp(date)
    # DEFECT FIXED 2026-09-13. This read `d - pd.offsets.MonthBegin(1)`, which
    # from a mid-month date rolls back to the FIRST OF THE SAME MONTH, not to the
    # previous month — so the day <= 15 branch was a no-op and the convention the
    # docstring describes was never applied. It bit exactly one read date, and it
    # is the one Martin queried: the 2021-04-04 frame was compared against the
    # END-OF-APRIL water table (median -0.260 m, 14 wells at or above ground)
    # when the frame was taken on the 4th, eleven days after 2021-03-24, whose
    # end-of-March level is median +0.020 m with 41 wells at or above ground. The
    # warren does not drain that fast, and it did not: the model was reading a
    # month into the frame's future.
    if d.day <= 15:
        prev = d.replace(day=1) - pd.Timedelta(days=1)
        key = pd.Timestamp(prev.year, prev.month, 1)
    else:
        key = pd.Timestamp(d.year, d.month, 1)
    row = lev[lev["month"] == key]
    out = []
    if not len(row):
        return pd.DataFrame(columns=["well", "h_m", "E", "N"])
    row = row.iloc[0]
    byname = {str(n).lower(): (e, nn) for n, e, nn
              in zip(wells["Name"], wells["E"], wells["N"])}
    for c in lev.columns:
        if c == "month":
            continue
        v = pd.to_numeric(pd.Series([row[c]]), errors="coerce").iloc[0]
        if pd.isna(v):
            continue
        en = byname.get(str(c).lower())
        if en is None:
            continue
        out.append({"well": c, "h_m": float(v), "E": en[0], "N": en[1]})
    return pd.DataFrame(out)


def _score(fg, lev, wells, date, gtr, usable, near_m, tol_m):
    """Score the flood bodies against the dipwell record for that month.

    PRECISION IS A LOWER BOUND AND RECALL IS NOT. Wells were sited at slack
    EDGES for ease of measurement (Martin, 2026-09-10; CEH1, CEH9 and NW6
    named), so a well can read below ground while its slack is flooded, and
    every such well scores as a FALSE POSITIVE when the method is right. Delta,
    which would correct it, is not known. The near-ground band is reported
    separately so the size of the effect is visible rather than asserted.
    """
    from shapely.geometry import Point                       # noqa: PLC0415
    wl = _well_levels(lev, wells, date)
    if not len(wl):
        return {"per_well": pd.DataFrame(),
                "summary": {"n_wells": 0, "recall": None, "precision": None,
                            "agreement": None, "tp": 0, "fp": 0, "fn": 0,
                            "tn": 0}}
    pts = gpd.GeoDataFrame(
        wl, geometry=[Point(x, y) for x, y in zip(wl["E"], wl["N"])], crs=OSGB)
    keep = []
    for _, r in pts.iterrows():
        c, r0 = ~gtr * (r["E"], r["N"])
        c, r0 = int(c), int(r0)
        keep.append(0 <= r0 < usable.shape[0] and 0 <= c < usable.shape[1]
                    and bool(usable[r0, c]))
    pts = pts[pd.Series(keep, index=pts.index)].copy()
    if not len(pts):
        return {"per_well": pd.DataFrame(),
                "summary": {"n_wells": 0, "recall": None, "precision": None,
                            "agreement": None, "tp": 0, "fp": 0, "fn": 0,
                            "tn": 0}}
    # A WELL IS NOT LOCALISED TO A POINT IN THIS FRAME. `tol_m` is the
    # registration's OWN median residual against the 88 surveyed positions, read
    # from the committed 41_03 — the frame cannot place a well better than that,
    # so a boundary drawn finer than it is spurious precision. It is not a
    # tuning knob: measured 2026-09-11, eleven of eleven false negatives at
    # strict containment had water within 10.1 m and six within 3.8 m, which is
    # the waterline running through the pipe, not a classification error. The
    # value is whatever Script 41 published; this tool does not choose it.
    j = gpd.sjoin_nearest(pts, fg[["body_id", "slack", "geometry"]], how="left",
                          max_distance=tol_m, distance_col="body_dist_m")
    j = j.sort_values("body_dist_m").drop_duplicates(subset=["well"])
    j["wet_pred"] = j["body_id"].notna()
    j["wet_truth"] = j["h_m"] >= 0.0
    j["near_ground"] = j["h_m"].abs() <= near_m
    tp = int((j.wet_truth & j.wet_pred).sum())
    fp = int((~j.wet_truth & j.wet_pred).sum())
    fn = int((j.wet_truth & ~j.wet_pred).sum())
    tn = int((~j.wet_truth & ~j.wet_pred).sum())
    n = tp + fp + fn + tn
    per = j[["well", "h_m", "wet_truth", "wet_pred", "body_id", "slack",
             "body_dist_m", "near_ground"]].copy()
    per["body_dist_m"] = per["body_dist_m"].round(2)
    per["h_m"] = per["h_m"].round(3)
    return {"per_well": per.sort_values("well"),
            "summary": {
                "n_wells": n,
                "recall": round(tp / (tp + fn), 3) if (tp + fn) else None,
                "precision": round(tp / (tp + fp), 3) if (tp + fp) else None,
                "agreement": round((tp + tn) / n, 3) if n else None,
                "tp": tp, "fp": fp, "fn": fn, "tn": tn,
                "fp_near_ground": int((~j.wet_truth & j.wet_pred
                                       & j.near_ground).sum())}}


def phase9() -> int:
    """Delta, the slack-bottom offset, measured rather than surveyed.

    Delta_i = ground at the pipe - the floor of that well's own slack, so the
    slack floods when h_i >= -Delta_i. The Q4 analysis (2026-09-10) put this
    quantity beyond analysis and behind a field campaign: "the record gives
    differences; it cannot give the absolute, and no further analysis will. A
    tape at one well per group converts the lot." The flood read supplies the
    absolute, because a waterline is a contour.

    THREE UNITS ARE EMITTED, not one. Which polygon counts as "that well's own
    slack" is the whole question, and all three answers are written out so the
    choice is visible rather than buried:

      local  the DEM minimum within sqrt(SLACK_MIN_AREA_M2 / pi) of the well.
             NOT a chosen radius: SLACK_MIN_AREA_M2 is already committed as the
             smallest thing this project calls a slack, so that is the radius of
             the smallest slack, and a well's own floor must lie inside it.
      A      the smallest merge-tree node containing the well that still holds
             SLACK_MIN_DEPTH_M.
      B      the DEM minimum inside the well's own flood body, over the dates it
             was flooded.

    Measured 2026-09-11 against the July bound, which is the test below: local
    6 violations of 78, A 11 of 40, B 15 of 38, and the hollow's own floor - the
    unit phase 6 draws - 23 of 53. A fails where the hierarchy jumps: at CEH9
    the first ancestor holding 0.10 m is a 25,308-cell node. B fails because a
    flood body is the WATER's extent, which at high water spans several slacks.

    THE DEM OFFSET IS MEASURED HERE TOO, not assumed. At every flood body
    holding a gauged well, the waterline elevation - the median DEM value along
    the body's own outline - is compared with that well's own water surface,
    DGPS ground plus its reading. The median is the raster's local bias and it
    repeats per well across dates, which is what makes it the local ground
    rather than noise.

    TWO CHOICES IN THAT MEASUREMENT ARE PINNED, 2026-09-13, because both were
    being made by accident:

      1. **Only DGPS-surveyed ground contributes** (`PHASE9_BIAS_GROUND_SOURCES`).
         Where ground came from the DEM, the bias appears on both sides of the
         subtraction and cancels: those pairs returned -0.037 m at MAD 0.153
         against the DGPS pairs' +0.302 at 0.083, scattered about zero, which is
         what a cancelled measurement looks like. Excluding them tightens the
         scatter by a quarter. It is the scraped-well exclusion's own logic: a
         well whose ground has CHANGED since the LiDAR cannot measure the LiDAR,
         and neither can a well whose ground IS the LiDAR.
      2. **The basis is vp2** (`PHASE9_WATERLINE_BASIS`). This file previously
         took the tiles wherever they existed, while the committed constant was
         the vp2 number - so a re-run would have moved the bias from +0.282 to
         +0.220 with nothing recording the change. Three vp2 dates beat one tile
         date until more tile dates exist; switching is now an edit, not a side
         effect.

    UNCHANGED BY EITHER: the unthresholded level frame was tested and REJECTED
    here. It adds two pairs, both LiDAR-ground, because a pair needs a well at or
    above ground ON A READ DATE and the short-record wells span none; it moved the
    constant 1 cm and widened the MAD from 0.111 to 0.141. `01_wells_all.csv` is
    right for phase 13 and wrong for this, which is D-164's lesson pointing the
    other way: the basis follows what the analysis does with it.
    """
    import math                                              # noqa: PLC0415
    from rasterio.mask import mask as rio_mask2              # noqa: PLC0415
    from shapely.geometry import Point                       # noqa: PLC0415

    from utils.config import (SCRAPE_DEM_CORRECTION_M,       # noqa: PLC0415
                              SLACK_MIN_AREA_M2, SLACK_MIN_DEPTH_M)
    from utils.slacks import merge_tree                      # noqa: PLC0415

    phase(9, "Delta — the slack-bottom offset, from the flood read")
    wells = pd.read_csv(REPO / "outputs" / "01_well_elevations.csv",
                        float_precision="round_trip")
    lev = pd.read_csv(REPO / "outputs" / "01_wells_clean.csv",
                      float_precision="round_trip")
    lev = lev.rename(columns={lev.columns[0]: "month"})
    lev["month"] = pd.to_datetime(lev["month"])
    en = {str(n).lower(): (e, nn) for n, e, nn
          in zip(wells["Name"], wells["E"], wells["N"])}
    ground = {str(n).lower(): float(g) for n, g
              in zip(wells["Name"], wells["ground_elev_m"])}
    gsrc = {str(n).lower(): str(v).lower() for n, v
            in zip(wells["Name"], wells["ground_source"])}

    # THE WATERLINE BASIS IS PINNED, so phase 9 measures Delta from the tile polygons
    # where they exist and falls back to the vp2 ones. Which it used is stated,
    # because Delta is read off the waterline and the waterline's precision is
    # the whole reason the tiles were captured.
    basis = PHASE9_WATERLINE_BASIS
    if basis == "tiles":
        floods = sorted(OUT.glob("W94_08_flood_tiles_*.geojson"))
    else:
        floods = [q for q in sorted(OUT.glob("W94_08_flood_*.geojson"))
                  if "_tiles_" not in q.name]
    if floods:
        info(f"Delta is measured from the {basis} flood read")
    if not floods:
        warn("phase 8 has not run: no flood polygons to measure from")
        return 1
    info(f"{len(floods)} flood read(s): "
         f"{', '.join(f.stem.split('flood_')[1] for f in floods)}")

    ds = rasterio.open(DATA_DEM)

    # ── the raster's local bias, from the waterlines ────────────────────────
    pairs = []
    for f in floods:
        date = f.stem.split("flood_")[1]
        fg = gpd.read_file(f).set_crs(OSGB, allow_override=True)
        wl = _well_levels(lev, wells, date)
        for _, r in wl.iterrows():
            nm = str(r["well"]).lower()
            if r["h_m"] < 0 or nm not in ground:
                continue
            p = Point(r["E"], r["N"])
            d = fg.distance(p)
            i = int(d.idxmin())
            if d.min() > 5.0:
                continue
            geom = fg.geometry.loc[i]
            xs, ys = [], []
            for poly in (list(geom.geoms) if geom.geom_type == "MultiPolygon"
                         else [geom]):
                cc = list(poly.exterior.coords)
                xs += [c[0] for c in cc]
                ys += [c[1] for c in cc]
            v = np.array([q[0] for q in ds.sample(zip(xs, ys))], float)
            v = v[np.isfinite(v)]
            if ds.nodata is not None:
                v = v[v != ds.nodata]
            if v.size <= 8:
                continue
            pairs.append({"date": date, "well": r["well"],
                          "waterline_m": round(float(np.median(v)), 3),
                          "outline_iqr_m": round(float(np.percentile(v, 75)
                                                       - np.percentile(v, 25)), 3),
                          "well_surface_m": round(ground[nm] + r["h_m"], 3),
                          "bias_m": round(float(np.median(v))
                                          - (ground[nm] + r["h_m"]), 3),
                          "ground_source": gsrc.get(nm, "unknown"),
                          "scraped": nm in SCRAPE_DEM_CORRECTION_M})
    if not pairs:
        warn("no flood body holds a gauged well; cannot measure the bias")
        return 1
    P = pd.DataFrame(pairs)
    p = OUT / "W94_11_waterline_vs_well.csv"
    P.to_csv(p, index=False)
    saved(p.name)
    clean = P[(~P["scraped"])
              & P["ground_source"].isin(PHASE9_BIAS_GROUND_SOURCES)]
    dropped = P[~P.index.isin(clean.index)]
    off = float(clean["bias_m"].median())
    mad = float((clean["bias_m"] - off).abs().median())
    step(f"raster bias from {len(clean)} waterline/well pair(s) over "
         f"{clean['date'].nunique()} date(s), basis {basis}, ground "
         f"{'/'.join(PHASE9_BIAS_GROUND_SOURCES)}: {off:+.3f} m, MAD {mad:.3f}")
    if len(dropped):
        by = dropped.groupby("ground_source")["bias_m"].agg(["size", "median"])
        for src_, r_ in by.iterrows():
            info(f"  excluded {int(r_['size'])} pair(s) on ground_source="
                 f"{src_} (median {r_['median']:+.3f} m) — a well whose ground "
                 f"came from the DEM cannot measure the DEM")
        n_scr = int(dropped["scraped"].sum())
        if n_scr:
            info(f"  and {n_scr} scraped pair(s), as before")
    rep = P.groupby("well")["bias_m"].agg(["size", "std"])
    rep = rep[rep["size"] >= 2]
    if len(rep):
        info(f"  it REPEATS per well: {len(rep)} well(s) on 2+ dates, median "
             f"within-well sd {rep['std'].median():.3f} m — the offset is the "
             f"local ground, not noise")

    # ── the three units ─────────────────────────────────────────────────────
    R = math.sqrt(SLACK_MIN_AREA_M2 / math.pi)
    info(f"local unit radius = sqrt(SLACK_MIN_AREA_M2 / pi) = "
         f"sqrt({SLACK_MIN_AREA_M2:.0f} / pi) = {R:.2f} m — derived, not chosen")

    def _corrected(nm, floor_raw):
        """Debias, then remove ground cut AFTER the LiDAR was flown."""
        return floor_raw - off - SCRAPE_DEM_CORRECTION_M.get(nm, 0.0)

    local = {}
    for nm, q in en.items():
        try:
            a, _ = rio_mask2(ds, [Point(*q).buffer(R).__geo_interface__],
                             crop=True, filled=True, nodata=np.nan)
        except Exception:                                     # noqa: BLE001
            continue
        z = a[0][np.isfinite(a[0])]
        if z.size < 3:
            continue
        local[nm] = _corrected(nm, float(np.nanmin(z)))

    unitB = {}
    for f in floods:
        fg = gpd.read_file(f).set_crs(OSGB, allow_override=True)
        for nm, q in en.items():
            p_ = Point(*q)
            d = fg.distance(p_)
            i = int(d.idxmin())
            if d.min() > 3.93:
                continue
            try:
                a, _ = rio_mask2(ds, [fg.geometry.loc[i].__geo_interface__],
                                 crop=True, filled=True, nodata=np.nan)
            except Exception:                                 # noqa: BLE001
                continue
            z = a[0][np.isfinite(a[0])]
            if z.size >= 5:
                unitB.setdefault(nm, []).append(
                    _corrected(nm, float(np.nanmin(z))))
    unitB = {k: float(np.median(v)) for k, v in unitB.items()}

    site = warren_on(str(P["date"].max()))
    db = ds.bounds
    want = site.bounds
    rb = (max(want[0], db.left), max(want[1], db.bottom),
          min(want[2], db.right), min(want[3], db.top))
    win = rasterio.windows.from_bounds(*rb, ds.transform)
    arr = ds.read(1, window=win).astype("float32")
    tr = ds.window_transform(win)
    leafc, nodes = merge_tree(arr)
    Nn = len(nodes)
    par = np.fromiter((nd["parent"] for nd in nodes), dtype=np.int64, count=Nn)
    fl = np.fromiter((nd["floor_m"] for nd in nodes), dtype=float, count=Nn)
    ml = np.fromiter((nd["merge_level_m"] for nd in nodes), dtype=float, count=Nn)
    op = np.fromiter((nd["open"] for nd in nodes), dtype=bool, count=Nn)
    dep = np.where(op, -1.0, ml - fl)
    inv = ~tr
    unitA = {}
    for nm, q in en.items():
        c, r0 = inv * q
        c, r0 = int(c), int(r0)
        if not (0 <= r0 < arr.shape[0] and 0 <= c < arr.shape[1]):
            continue
        cur = int(leafc[r0, c])
        pick = None
        for _ in range(200):
            if dep[cur] >= SLACK_MIN_DEPTH_M:
                pick = cur
                break
            nxt = int(par[cur])
            if nxt < 0 or nxt == cur:
                break
            cur = nxt
        if pick is not None:
            unitA[nm] = _corrected(nm, float(fl[pick]))
    ds.close()

    # ── the test: the July bound, which has no DEM and no imagery in it ─────
    jul = lev[lev["month"].dt.month == 7].drop(columns="month")
    jul = jul.apply(pd.to_numeric, errors="coerce")
    bound = {str(k).lower(): -float(v) for k, v in jul.max().items()
             if pd.notna(v)}
    n_jul = int((lev["month"].dt.month == 7).sum())
    info(f"the July bound, from {n_jul} July(s): no well reaches ground in any "
         f"of them, so Delta < -h in every one")

    rows = []
    for nm in sorted(en):
        rows.append({
            "well": nm,
            "ground_m": round(ground.get(nm, float("nan")), 3),
            "delta_local_m": (round(ground[nm] - local[nm], 3)
                              if nm in local and nm in ground else None),
            "delta_unitA_m": (round(ground[nm] - unitA[nm], 3)
                              if nm in unitA and nm in ground else None),
            "delta_unitB_m": (round(ground[nm] - unitB[nm], 3)
                              if nm in unitB and nm in ground else None),
            "july_bound_m": (round(bound[nm], 3) if nm in bound else None),
            "scrape_correction_m": SCRAPE_DEM_CORRECTION_M.get(nm, 0.0),
        })
    D = pd.DataFrame(rows)
    for u in ("local", "unitA", "unitB"):
        D[f"violates_{u}"] = (D[f"delta_{u}_m"].notna()
                              & D["july_bound_m"].notna()
                              & (D[f"delta_{u}_m"] > D["july_bound_m"]))
    p = OUT / "W94_14_delta.csv"
    D.to_csv(p, index=False)
    saved(p.name)

    step("Delta by unit, scored against the July bound:")
    for u, lab in (("local", f"local DEM minimum, R = {R:.2f} m"),
                   ("unitA", "smallest merge-tree node holding "
                             f"{SLACK_MIN_DEPTH_M:.2f} m"),
                   ("unitB", "DEM minimum in the well's own flood body")):
        col = D[f"delta_{u}_m"]
        t = D[col.notna() & D["july_bound_m"].notna()]
        v = int(D[f"violates_{u}"].sum())
        info(f"  {lab:52s} n {int(col.notna().sum()):3d}  median "
             f"{col.median():6.3f}  violations {v:2d} / {len(t)}")
    bad = D[D["violates_local"]]
    if len(bad):
        info("  wells the local unit cannot satisfy:")
        for _, r in bad.iterrows():
            info(f"    {r['well']:10s} Delta {r['delta_local_m']:+.3f} against "
                 f"a bound of {r['july_bound_m']:+.3f}")
    info("DELTA IS NOT WRITTEN INTO ANY PIPELINE STORE by this tool. It is a "
         "measurement offered for adoption, and adoption is a decision.")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 18 — THE HOLLOW AS A DIPWELL (T-27)
# ─────────────────────────────────────────────────────────────────────────────
# Script 11b already answers, for every dipwell, "how much cumulative winter
# rainfall brings the water table to this surface" — the iterated closed form of
# Section 3.6.3, shipped in forecaster.html. Martin, 2026-09-13: "aren't we
# replicating the work of the flood forecaster?" Largely, yes.
#
# The collapsed form is P_flood = A·d + B, where d is the depth of the
# antecedent water table below THE SURFACE YOU WANT WETTED. For a well that
# surface is its own ground. NOTHING IN THE DERIVATION REQUIRES IT TO BE, and
# that is the whole of this phase: put the hollow floor there instead. The area
# mapping is then DERIVED from the DEM's hypsometry rather than fitted to four
# imagery dates, which is what dissolves the n = 3 problem that killed phase 17
# and turns the imagery from training data into a test set.

PFLOOD_IDW_POWER = 2.0
PFLOOD_SENS_POWERS = (1.0, 2.0, 3.0)
PFLOOD_SUMMER_MONTHS = (8, 9)
PFLOOD_CLUSTER_MASS_MIN = 0.50   # below this the hollow's cluster is ambiguous
PFLOOD_C1_CAVEAT_WELL = "ceh11"  # C1 by SSM behaviour, 2.1 km from the lake


def _pflood_wells():
    """Per-well cluster and antecedent geometry, from Script 11b's committed CSV.

    `dem` and `depth_bg` are the two numbers this phase interpolates: the well's
    ground elevation and the depth of its MEAN SUMMER MINIMUM below that ground.
    Both are already in the file that feeds the forecaster, so nothing here
    re-derives a published quantity.
    """
    from utils.paths import OUT_11B_PFLOOD_PER_WELL              # noqa: PLC0415
    P = pd.read_csv(OUT_11B_PFLOOD_PER_WELL, float_precision="round_trip")
    P["well"] = P["well"].astype(str).str.lower().str.strip()
    P = P.dropna(subset=["E", "N", "dem", "depth_bg", "cluster"])
    return P.reset_index(drop=True)


def _pflood_cluster_betas():
    """Cluster β in the units the closed form wants: metres of head per mm."""
    from utils.paths import OUT_03_MECHANISTIC_TABLE             # noqa: PLC0415
    cc = pd.read_csv(OUT_03_MECHANISTIC_TABLE, float_precision="round_trip")
    out = {}
    for _, r in cc.iterrows():
        cid = int(str(r["Cluster"]).lstrip("Cc"))
        out[cid] = {"b1": float(r["beta_1_recharge"]) / 1000.0,
                    "b2": float(r["beta_2_atmospheric_draw"]) / 1000.0,
                    "b3": abs(float(r["beta_3_drainage"])),
                    "label": str(r["Cluster_Label"])}
    return out


def _pflood_climate():
    """(actual monthly series, rainfall climatology, PET climatology)."""
    from utils.paths import INT_REGIONAL_AVG                     # noqa: PLC0415
    ra = pd.read_csv(INT_REGIONAL_AVG, parse_dates=["Date"],
                     float_precision="round_trip")
    P_act = {(d.year, d.month): float(v)
             for d, v in zip(ra["Date"], ra["P_mm"]) if pd.notna(v)}
    E_act = {(d.year, d.month): float(v)
             for d, v in zip(ra["Date"], ra["PET_mm"]) if pd.notna(v)}
    P_clim = ra.groupby(ra["Date"].dt.month)["P_mm"].mean().to_dict()
    E_clim = ra.groupby(ra["Date"].dt.month)["PET_mm"].mean().to_dict()

    # Months later than the pipeline's frozen climate input reach this phase the
    # same way the well readings do (D-166) and no other way. RAINFALL ONLY: a
    # Thornthwaite PET needs the whole year's mean temperatures for its heat
    # index, and the calibration file carries one month, so the month's PET
    # CLIMATOLOGY stands in and every row that used it says so.
    from utils.paths import DATA_FLOOD_CAL_CLIMATE                # noqa: PLC0415
    borrowed = set()
    if DATA_FLOOD_CAL_CLIMATE.exists():
        cc = pd.read_csv(DATA_FLOOD_CAL_CLIMATE, float_precision="round_trip")
        rain = [c for c in cc.columns if "rain" in str(c).lower()]
        for _, r in cc.iterrows():
            try:
                d = pd.Timestamp(pd.to_datetime(str(r[cc.columns[0]]),
                                                format="%b %y"))
            except Exception:                                     # noqa: BLE001
                continue
            k = (d.year, d.month)
            if k in P_act or not rain:
                continue
            P_act[k] = float(r[rain[0]])
            E_act[k] = float(E_clim[d.month])
            borrowed.add(k)
            info(f"  calibration climate {d:%Y-%m} added from "
                 f"{DATA_FLOOD_CAL_CLIMATE.name}: P {P_act[k]:.1f} mm, PET from "
                 f"the month's climatology ({E_act[k]:.1f} mm) — NOT a pipeline "
                 f"input")
    return P_act, E_act, P_clim, E_clim, borrowed


def _pflood_peak_months():
    from utils.paths import INT_CLUSTER_PEAK_MONTHS              # noqa: PLC0415
    cp = pd.read_csv(INT_CLUSTER_PEAK_MONTHS)
    return {int(r["cluster_id"]): int(r["peak_month"])
            for _, r in cp.iterrows()}


def _horizon_truncated(peak_month, stop_month=None):
    """October to the cluster's peak, TRUNCATED AT THE READ MONTH (Martin's call).

    A late-March read sits past C1 and C2's January peak and inside C3-C5's
    February one. Truncation keeps every read date usable and is the same closed
    form over a shorter month list — but it means C1 and C2 are evaluated over a
    horizon their own peak month says is already over, and that asymmetry is
    stated on every output rather than smoothed away.
    """
    from utils.model_utils import horizon_months                 # noqa: PLC0415
    hz = horizon_months(int(peak_month))
    if stop_month is None:
        return hz, False
    if stop_month in hz:
        return hz[:hz.index(stop_month) + 1], False
    return hz, True                    # read is past the peak: horizon runs out


def _horizon_read(stop_month):
    """October to the READ MONTH, however far past the cluster peak that is.

    Martin's ruling was to truncate at the read date. Truncation is only half of
    it: a read INSIDE the horizon cuts it short, and a read PAST the peak must
    EXTEND it, because the question Mode V asks is what the water table was doing
    ON THE DAY THE PHOTOGRAPH WAS TAKEN. The first run of this phase used the
    cluster horizon for both and so scored four spring and summer dry controls at
    the FOLLOWING JANUARY OR FEBRUARY PEAK - it predicted 33-53 ha of water in
    photographs with none, and failed its own dry-control gate at 1.31 : 1 for
    that reason alone. Extending is not extrapolation: the recurrence is defined
    for every month and is driven here by that month's measured P and PET. What
    the cluster peak still decides is Mode C, where the question IS the winter
    maximum.
    """
    months, m = [], 10
    for _ in range(12):
        months.append(m)
        if m == int(stop_month):
            break
        m = (m % 12) + 1
    return months


def _pflood_hypsometry(hollows, ds, bias_m):
    """Each hollow's DEM cells, debiased and sorted — its hypsometric curve.

    THE AREA MAPPING LIVES HERE and nowhere else. Given a water level the
    threshold says is reached, the flooded area inside a hollow is the count of
    its own cells below that level times the cell area. No interpolation, no
    fitting, no constant chosen to make an area come out right.
    """
    from rasterio.mask import mask as rio_mask                   # noqa: PLC0415
    cell = abs(ds.transform.a * ds.transform.e)
    out = {}
    for _, h in hollows.iterrows():
        if pd.isna(h.get("slack")):
            continue
        try:
            a, _ = rio_mask(ds, [h.geometry.__geo_interface__], crop=True,
                            filled=True, nodata=np.nan)
        except Exception:                                        # noqa: BLE001
            continue
        z = a[0][np.isfinite(a[0])]
        if ds.nodata is not None:
            z = z[z != ds.nodata]
        if z.size < 3:
            continue
        out[int(h["slack"])] = (np.sort(z.astype(float)) - bias_m, cell)
    return out


def _pflood_geometry(hollows, hyps, W, power=PFLOOD_IDW_POWER, k=0,
                     depth_col="depth_bg"):
    """d at every hollow floor, and the cluster whose dynamics it inherits.

    d = IDW(well depth below ground) + (floor - IDW(well ground elevation)).

    THE INTERPOLATED QUANTITY IS A DEPTH, NOT AN ELEVATION, and that is
    deliberate. The two forms are algebraically identical; only the error
    structure differs. Phase 16 measured what interpolating an ABSOLUTE water
    table costs here - 714 of 1,236 observed-wet slacks missed by a median
    1.278 m, the misses at a median floor of 9.10 m AOD against 4.17 m, the
    shortfall correlating with distance to the nearest well at r = +0.51 - which
    is IDW flattening a mound. A depth field has a range of about 1.7 m across
    the site; the topography comes from the DEM, where it is known to 2 m.
    """
    ids = sorted(hyps)
    cen = {int(r["slack"]): r.geometry.centroid
           for _, r in hollows.iterrows() if pd.notna(r.get("slack"))}
    X = np.array([cen[i].x for i in ids], float)
    Y = np.array([cen[i].y for i in ids], float)
    wx, wy = W["E"].to_numpy(float), W["N"].to_numpy(float)

    if k and k < len(W):
        dep, dem = [], []
        for x, y in zip(X, Y):
            o = np.argsort((wx - x) ** 2 + (wy - y) ** 2)[:k]
            dep.append(_idw(wx[o], wy[o], W[depth_col].to_numpy(float)[o],
                            [x], [y], power=power)[0])
            dem.append(_idw(wx[o], wy[o], W["dem"].to_numpy(float)[o],
                            [x], [y], power=power)[0])
        dep, dem = np.asarray(dep), np.asarray(dem)
    else:
        dep = _idw(wx, wy, W[depth_col].to_numpy(float), X, Y, power=power)
        dem = _idw(wx, wy, W["dem"].to_numpy(float), X, Y, power=power)

    floor = np.array([float(hyps[i][0][0]) for i in ids])
    dz = floor - dem
    d = dep + dz

    # cluster: nearest well, with the ambiguity reported rather than hidden
    d2 = ((wx[:, None] - X[None, :]) ** 2 + (wy[:, None] - Y[None, :]) ** 2)
    near = np.argmin(d2, axis=0)
    cl = W["cluster"].to_numpy()[near].astype(int)
    nm = W["well"].to_numpy()[near]
    wgt = 1.0 / (np.sqrt(d2) + 1e-6) ** power
    mass = {}
    for c in sorted(set(W["cluster"].astype(int))):
        mass[c] = wgt[(W["cluster"].astype(int) == c).to_numpy()].sum(axis=0)
    tot = np.sum([mass[c] for c in mass], axis=0)
    top = np.max([mass[c] / tot for c in mass], axis=0)
    return pd.DataFrame({"slack": ids, "E": X, "N": Y, "floor_m": floor,
                         "dem_interp_m": dem, "depth_interp_m": dep,
                         "dz_m": dz, "d_m": d, "cluster": cl,
                         "nearest_well": nm, "cluster_mass": top,
                         "cluster_ambiguous": top < PFLOOD_CLUSTER_MASS_MIN,
                         "c1_via_caveat_well": (cl == 1)
                         & (nm == PFLOOD_C1_CAVEAT_WELL)})


def _pflood_iterate(d, b1, b2, b3, months, P, E, datum):
    """The SSM recurrence, run forward from the floor. Returns head above floor.

    h(t) = (1-b3)*h(t-1) + b1*P(t) - b2*PET(t) - b3*D, the recurrence
    model_utils.pflood_lambda solves in closed form. Run here with the year's
    ACTUAL monthly rainfall and PET instead of a multiplier on climatology, so
    Mode V asks nothing of the rainfall's within-winter shape. The self-test in
    phase18() drives this loop with the closed form's own solution and requires
    the two to agree, which is what stops the recurrence drifting from 11b's.
    """
    h = -float(d)
    for m in months:
        h = (1.0 - b3) * h + b1 * P[m] - b2 * E[m] - b3 * datum
    return h


def _pflood_area(hyps_entry, level):
    """Hectares of a hollow below a level, from its own cells."""
    z, cell = hyps_entry
    return float(np.searchsorted(z, level) * cell / 1e4)


def _pflood_read_dates():
    """The imagery reads, plus the dry controls, as (date, path-or-None)."""
    reads = {}
    for f in sorted(OUT.glob("W94_08_flood_*.geojson")):
        if "_tiles_" in f.name:
            continue
        reads[f.stem.split("flood_")[1]] = f
    for d in DRY_CALIBRATION_DATES:
        reads.setdefault(d, None)
    return dict(sorted(reads.items()))


def _pflood_bucket(date_str):
    """(winter-start year, read month) under Script 01's bucketing."""
    d = pd.Timestamp(date_str)
    m = d.month if d.day > 15 else (d - pd.Timedelta(days=d.day)).month
    y = d.year if (d.day > 15 or d.month > 1) else d.year - 1
    return (y if m >= 10 else y - 1), m


def _pflood_antecedent(lev, W, winter_year):
    """Each well's OBSERVED summer minimum before that winter, as a depth.

    Mode V asks what the aquifer actually did, so the antecedent state is that
    year's August-September minimum and not the climatological one. A well with
    no reading in either month keeps its published mean, and the count of those
    is reported: at the early end of the record most wells fall back, which is
    the same thinning network that made the phase 14 series two-based.
    """
    sub = lev[(lev["month"].dt.year == winter_year)
              & (lev["month"].dt.month.isin(PFLOOD_SUMMER_MONTHS))]
    obs, fell = [], 0
    for _, r in W.iterrows():
        w = r["well"]
        v = np.nan
        if w in sub.columns and len(sub):
            s = pd.to_numeric(sub[w], errors="coerce").dropna()
            if len(s):
                v = -float(s.min())          # h is negative below ground
        if not np.isfinite(v):
            v = float(r["depth_bg"])
            fell += 1
        obs.append(v)
    out = W.copy()
    out["depth_year"] = obs
    return out, fell


def phase18(mode="both", power=PFLOOD_IDW_POWER, sens=False) -> int:
    """The hollow as a dipwell: Script 11b's threshold, put on a slack floor.

    MODE C is the publishable product - which hollows flood in an average
    winter, from the climatological summer minimum and the collapsed form
    P_flood = A*d + B. MODE V is what earns it: the same construction with that
    year's OBSERVED summer minimum and that winter's ACTUAL monthly rainfall and
    PET, scored against every imagery read and against the four dry controls,
    which must come out near zero. That gate is what --form depth failed.

    NOTHING IS FITTED TO THE IMAGERY. A, B, the horizon, the betas and the
    climatology are committed pipeline outputs; the geometry is the DEM. Four
    dates are a thin training set and an adequate test set, which is the whole
    reason for inverting the order after phase 17.

    WHAT IT DOES NOT DO. It predicts flooding IN MAPPED HOLLOWS: phase 16 put
    37.7 % of the 2021-03-24 water outside any closed basin, and no hollow-based
    method recovers that ground. The interpolated depth field is the dominant
    uncertainty AND IT IS MULTIPLIED BY A - at 174-383 mm/m a 0.3 m error in d
    is 52-115 mm of P_flood - which is why --sens exists and why its spread is
    quoted beside any area this produces.
    """
    from utils.config import DRAINAGE_DATUM                      # noqa: PLC0415
    from utils.model_utils import pflood_lambda                  # noqa: PLC0415
    phase(18, "The hollow as a dipwell — 11b's threshold on a slack floor")

    W = _pflood_wells()
    betas = _pflood_cluster_betas()
    peaks = _pflood_peak_months()
    P_act, E_act, P_clim, E_clim, borrowed = _pflood_climate()
    step(f"{len(W)} well(s) from 11b_03_pflood_per_well.csv; clusters "
         + ", ".join(f"C{c} {n}" for c, n in
                     sorted(W['cluster'].astype(int).value_counts().items())))

    # ── the self-test: this recurrence must be 11b's ─────────────────────
    worst = 0.0
    for c, b in betas.items():
        hz, _ = _horizon_truncated(peaks[c])
        r = pflood_lambda(h_target=0.0, h_0=-1.0, b1=b["b1"], b2=b["b2"],
                          b3=b["b3"], months=hz, P_clim=P_clim,
                          PET_clim=E_clim)
        Pl = {m: r["lam"] * P_clim[m] for m in hz}
        worst = max(worst, abs(_pflood_iterate(1.0, b["b1"], b["b2"], b["b3"],
                                               hz, Pl, E_clim, DRAINAGE_DATUM)))
    if worst > 1e-9:
        warn(f"the forward recurrence disagrees with the closed form by "
             f"{worst:.3e} m — phase 18 is NOT 11b and must not be used")
        return 1
    info(f"self-test: the forward recurrence reproduces 11b's closed form to "
         f"{worst:.1e} m at every cluster")

    hol_p = OUT / "W94_06_hollows.geojson"
    hollows = gpd.read_file(hol_p).set_crs(OSGB, allow_override=True)
    ds = rasterio.open(DATA_DEM)
    hyps = _pflood_hypsometry(hollows, ds, PHASE9_DEM_BIAS_M)
    ds.close()
    rim = {i: float(hyps[i][0][-1]) for i in hyps}
    step(f"{len(hyps)} hollow(s) with a hypsometric curve, DEM bias "
         f"{PHASE9_DEM_BIAS_M:+.3f} m (D-165)")

    # ── MODE C — the climatological map ──────────────────────────────────
    G = _pflood_geometry(hollows, hyps, W, power=power)
    AB = {}
    for c, b in betas.items():
        hz, _ = _horizon_truncated(peaks[c])
        r = pflood_lambda(h_target=0.0, h_0=0.0, b1=b["b1"], b2=b["b2"],
                          b3=b["b3"], months=hz, P_clim=P_clim,
                          PET_clim=E_clim)
        AB[c] = (float(r["slope_A"]), float(r["intercept_B"]),
                 float(r["P_clim_total"]), len(hz), peaks[c])
    rows = []
    for _, g in G.iterrows():
        c = int(g["cluster"])
        if c not in AB:
            continue
        A, B, Pc, n, pk = AB[c]
        pf = A * float(g["d_m"]) + B
        head = (Pc - pf) / A
        lvl = min(float(g["floor_m"]) + max(head, 0.0), rim[int(g["slack"])])
        rows.append({
            "slack": int(g["slack"]), "E": round(float(g["E"]), 1),
            "N": round(float(g["N"]), 1), "cluster": c,
            "cluster_label": betas[c]["label"],
            "nearest_well": g["nearest_well"],
            "floor_m": round(float(g["floor_m"]), 3),
            "dem_interp_m": round(float(g["dem_interp_m"]), 3),
            "depth_interp_m": round(float(g["depth_interp_m"]), 3),
            "dz_m": round(float(g["dz_m"]), 3),
            "d_m": round(float(g["d_m"]), 3),
            "slope_A_mm_per_m": round(A, 3), "intercept_B_mm": round(B, 3),
            "horizon_n_months": n, "peak_month": pk,
            "P_clim_total_mm": round(Pc, 3),
            "pflood_mm": round(pf, 3),
            "floods_average_winter": bool(pf <= Pc),
            "head_above_floor_m": round(head, 3),
            "area_ha_average_winter": round(
                _pflood_area(hyps[int(g["slack"])], lvl) if head > 0 else 0.0, 4),
            "cluster_mass": round(float(g["cluster_mass"]), 3),
            "cluster_ambiguous": bool(g["cluster_ambiguous"]),
            "c1_via_caveat_well": bool(g["c1_via_caveat_well"]),
        })
    C = pd.DataFrame(rows)
    p = OUT / "W94_90_pflood_per_hollow.csv"
    C.to_csv(p, index=False)
    saved(f"{p.name}  ({len(C)} hollow(s))")
    step(f"MODE C: {int(C['floods_average_winter'].sum())} of {len(C)} hollow(s) "
         f"flood in an average winter, {C['area_ha_average_winter'].sum():.2f} ha; "
         f"P_flood median {C['pflood_mm'].median():.0f} mm "
         f"(wells: {W['pflood_mm'].median():.0f} mm)")
    info(f"  {int(C['cluster_ambiguous'].sum())} hollow(s) with an ambiguous "
         f"cluster (top mass < {PFLOOD_CLUSTER_MASS_MIN:.2f}); "
         f"{int(C['c1_via_caveat_well'].sum())} assigned C1 through "
         f"{PFLOOD_C1_CAVEAT_WELL} — 2.1 km from the lake and below lake level, "
         f"so no lake-edge reading of those")

    if mode == "C":
        return 0

    # ── MODE V — the same construction, year by year, against the reads ──
    lev = _level_frame()
    V = []
    for date, path in _pflood_read_dates().items():
        wy, rm = _pflood_bucket(date)
        Wy, fell = _pflood_antecedent(lev, W, wy)
        Gy = _pflood_geometry(hollows, hyps, Wy, power=power,
                              depth_col="depth_year")
        pred, n_wet, past = 0.0, 0, False
        for _, g in Gy.iterrows():
            c = int(g["cluster"])
            if c not in betas:
                continue
            hz = _horizon_read(rm)
            past = past or (rm not in _horizon_truncated(peaks[c])[0])
            try:
                Pm = {m: P_act[(wy if m >= 10 else wy + 1, m)] for m in hz}
                Em = {m: E_act[(wy if m >= 10 else wy + 1, m)] for m in hz}
            except KeyError:
                continue
            b = betas[c]
            h = _pflood_iterate(float(g["d_m"]), b["b1"], b["b2"], b["b3"],
                                hz, Pm, Em, DRAINAGE_DATUM)
            if h > 0:
                n_wet += 1
                sid = int(g["slack"])
                pred += _pflood_area(hyps[sid],
                                     min(float(g["floor_m"]) + h, rim[sid]))
        obs_tot = obs_hol = np.nan
        if path is not None:
            r = gpd.read_file(path).set_crs(OSGB, allow_override=True)
            u = r.geometry.union_all()
            obs_tot = float(u.area / 1e4)
            obs_hol = float(sum(hollows.geometry.intersection(u).area) / 1e4)
        else:
            obs_tot = obs_hol = 0.0
        hz0 = _horizon_read(rm)
        Pr = sum(P_act.get((wy if m >= 10 else wy + 1, m), np.nan) for m in hz0)
        V.append({"date": date, "winter_start": wy, "read_month": rm,
                  "pet_borrowed_months": sum(
                      1 for m in hz0
                      if (wy if m >= 10 else wy + 1, m) in borrowed),
                  "dry_control": date in DRY_CALIBRATION_DATES,
                  "wells_fallback": fell, "n_wells": len(W),
                  "horizon_n_months": len(hz0),
                  "realised_P_mm": round(float(Pr), 1),
                  "past_peak_month": past,
                  "hollows_flooded": n_wet,
                  "predicted_ha": round(pred, 3),
                  "observed_ha_in_hollows": round(obs_hol, 3),
                  "observed_ha_total": round(obs_tot, 3)})
        info(f"  {date}  predicted {pred:7.2f} ha over {n_wet:4d} hollow(s)   "
             f"observed {obs_hol:7.2f} ha in hollows ({obs_tot:6.2f} total)"
             + ("   [DRY CONTROL]" if date in DRY_CALIBRATION_DATES else "")
             + (f"   [{fell} well(s) on the climatological mean]" if fell else ""))
    D = pd.DataFrame(V)
    p = OUT / "W94_91_pflood_validation.csv"
    D.to_csv(p, index=False)
    saved(p.name)

    wet = D[~D["dry_control"]]
    dry = D[D["dry_control"]]
    if len(wet) and len(dry):
        margin = (wet["predicted_ha"].max() / dry["predicted_ha"].max()
                  if dry["predicted_ha"].max() > 0 else np.inf)
        step(f"THE GATE: wettest {wet['predicted_ha'].max():.2f} ha against a "
             f"worst dry control of {dry['predicted_ha'].max():.2f} ha — margin "
             f"{margin:.2f} : 1 (DRY_CONTROL_MIN_RATIO "
             f"{DRY_CONTROL_MIN_RATIO:.2f})")
        if margin < DRY_CONTROL_MIN_RATIO:
            warn("MODE V FAILS ITS DRY-CONTROL GATE — do not adopt this")

    if sens:
        S = []
        for pw in PFLOOD_SENS_POWERS:
            Gs = _pflood_geometry(hollows, hyps, W, power=pw)
            tot = 0.0
            for _, g in Gs.iterrows():
                c = int(g["cluster"])
                if c not in AB:
                    continue
                A, B, Pc, _, _ = AB[c]
                head = (Pc - (A * float(g["d_m"]) + B)) / A
                if head > 0:
                    sid = int(g["slack"])
                    tot += _pflood_area(hyps[sid],
                                        min(float(g["floor_m"]) + head,
                                            rim[sid]))
            S.append({"idw_power": pw, "d_median_m": round(float(Gs["d_m"].median()), 3),
                      "area_ha_average_winter": round(tot, 3)})
            info(f"  IDW power {pw:.1f}: median d {Gs['d_m'].median():.3f} m, "
                 f"average-winter area {tot:.2f} ha")
        pd.DataFrame(S).to_csv(OUT / "W94_92_pflood_sensitivity.csv", index=False)
        saved("W94_92_pflood_sensitivity.csv")

    info("NOT ADOPTED and not in the pipeline. Mode C is a CLIMATOLOGICAL "
         "statement about mapped hollows; quote it only with the Mode V table "
         "and the sensitivity spread beside it.")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 19 — THE FALSE-WET MASK
# ─────────────────────────────────────────────────────────────────────────────
# MARTIN, 2026-09-14, correcting what the dry frames were FOR: "the reason why I
# gave you what I said were dry years and wet years was so you could mark bushes
# and other features which would be dark and look like wet patches and you could
# then digitize those as false wet features."
#
# They were never a zero-water gate on a MODEL. They are a measurement of the
# CLASSIFIER's false positives, and DRY_CONTROL_MIN_RATIO - invented here, not by
# Martin - scored the model against an assumption those frames were never asked
# to support. The first forced read of one settled it: 2009-04-20, a frame with
# no water in it, reads 87.86 ha, against 88.31 ha for the wettest frame in the
# corpus. Every area this tool has compared a model against carries that.

_fixed_cut = False   # set by phase 8 when --cut-z supplies the threshold
STANDING_WATER_BUFFER_M = 3.0    # a hand-drawn edge against a 2 m cell
FALSE_WET_MIN_DATES = 1          # 1 = union of the dry reads; 2 = seen twice
from utils.config import FLOOD_OTSU_MAX_Z as _GATE_Z    # noqa: E402
FALSE_WET_CUT_Z = _GATE_Z        # the gate: the shallowest cut ever accepted
FALSE_WET_FRAMES = ("2019-09-11", "2019-07-29", "2012-05-26", "2010-05-27",
                    "2009-04-20")
#   2019-09-11 is Martin's pick and the best of them: September, so the water
#   table is at its annual minimum and well below the surface, 10 registered
#   captures at ~1.0 m/px, residuals 0.47-2.1 m. Its OWN Otsu split is z = +1.79
#   and 2019-07-29's is +3.38 - both far above the dune median - which is why
#   neither may choose its own cut.


def phase19(min_dates=FALSE_WET_MIN_DATES, cut_z=FALSE_WET_CUT_Z) -> int:
    """The bushes: dark ground that is not water, marked and excluded.

    Martin, 2026-09-14, having looked at the fixed-cut read of 2019-09-11:
    "the other blue areas ... are trees and bushes, some of which I have already
    masked. you should mark these as bushes and exclude from the analysis." And,
    separately, "I have saved the places that have standing water in july 2019 as
    drinking_pool1.kml" — so the frame holds BOTH, and telling them apart is the
    whole job.

    THE CONSTRUCTION.
      bushes = (dry frames cut at a threshold they did not choose)
               + Martin's own warren_tree_mask.kml
               - the drinking pools

    Every dry frame is cut at `cut_z`, defaulting to FLOOD_OTSU_MAX_Z, the gate:
    the shallowest cut this project has ever accepted as water, and so the most
    generous a mask can be. A feature dark enough to pass it on a day with no
    water would have been read as water on 2021-03-24 (z = -1.318) or 2020-03-31
    (-1.116). That is the false positive.

    THE POOLS ARE SUBTRACTED FIRST AND WITH A BUFFER. They are real standing
    water, about 0.26 ha over five bodies, and a mask that swallowed them would
    blind every future read to standing water at exactly the places that hold it
    in a drought. The buffer is `STANDING_WATER_BUFFER_M`, because a hand-drawn
    pool edge and a 2 m classified cell will not agree to the metre and the
    error must fall on the side of keeping water.

    EXCLUSION, NOT SUBTRACTION. Phase 8 drops these cells from `usable` before
    any threshold is applied, so a bush cannot be classified as water on any
    frame and the correction cannot be forgotten, double-applied, or argued
    about later. The cost is stated on every run: a slack that floods UNDER a
    bush is unreadable there, so an area is a lower bound by whatever of the
    mask falls inside a hollow.
    """
    from shapely.ops import unary_union                       # noqa: PLC0415
    phase(19, "The bushes — dark ground that is not water")
    step(f"cut z = {cut_z:.3f} (the gate). The accepted wet frames cut at "
         f"-1.318 (2021-03-24, 36 wells at or above ground) and -1.116 "
         f"(2020-03-31, 6 wells), so anything passing this cut on a dry day "
         f"would have been read as water on either")

    parts, dates, missing = [], [], []
    for d in FALSE_WET_FRAMES:
        f = OUT / f"W94_08_flood_fixedz_{d}.geojson"
        if not f.exists():
            missing.append(d)
            continue
        g = gpd.read_file(f).set_crs(OSGB, allow_override=True)
        u = _valid(unary_union([_valid(x) for x in g.geometry]))
        parts.append(u)
        dates.append(d)
        info(f"  {d}: {len(g)} feature(s), {u.area / 1e4:7.2f} ha still "
             f"water-dark with no water present")
    if missing:
        warn(f"  no fixed-cut read for {', '.join(missing)} — run: "
             f"--phase 8 --cut-z {cut_z} "
             + " ".join(f"--date {d}" for d in missing))
    if not parts:
        warn("no fixed-cut dry reads at all; the mask cannot be built")
        return 1

    if min_dates <= 1:
        dark = _valid(unary_union(parts))
        basis = f"union of {len(parts)} dry frame(s) at z <= {cut_z}"
    else:
        pair = [_valid(parts[a].intersection(parts[b]))
                for a in range(len(parts)) for b in range(a + 1, len(parts))]
        pair = [g for g in pair if g is not None and not g.is_empty]
        dark = _valid(unary_union(pair)) if pair else None
        basis = f"dark on >= 2 of {len(parts)} dry frame(s) at z <= {cut_z}"
    if dark is None or dark.is_empty:
        step("nothing is water-dark on a dry frame at this cut")
        return 0

    hand = None
    if BUSH_MASK_KML.exists():
        hg = gpd.read_file(BUSH_MASK_KML).to_crs(OSGB)
        hand = _valid(unary_union([_valid(x) for x in hg.geometry]))
        info(f"  {BUSH_MASK_KML.name}: {hand.area / 1e4:.2f} ha already masked "
             f"by hand")
        dark = _valid(unary_union([dark, hand]))
        basis += f" + {BUSH_MASK_KML.name}"

    pool = _standing_water_geom()
    if pool is not None:
        n = len(list(pool.geoms)) if hasattr(pool, "geoms") else 1
        keep = pool.buffer(STANDING_WATER_BUFFER_M)
        lost = dark.intersection(keep).area / 1e4
        dark = _valid(dark.difference(keep))
        step(f"standing water held back: {n} pool(s), {pool.area / 1e4:.3f} ha, "
             f"buffered {STANDING_WATER_BUFFER_M:.1f} m — {lost:.3f} ha of the "
             f"dark ground was these and is NOT a bush")
        basis += f" - {STANDING_WATER_KML.name}"
    else:
        warn(f"  {STANDING_WATER_KML.name} is absent: standing water present in "
             f"a dry frame would be masked as bush, which is the one error this "
             f"phase must not make")

    M = gpd.GeoDataFrame({"basis": [basis], "cut_z": [cut_z],
                          "frames": [",".join(dates)]}, geometry=[dark],
                         crs=OSGB)
    q = OUT / "W94_95_bush_mask.geojson"
    M.to_file(q, driver="GeoJSON")
    saved(f"{q.name}  ({dark.area / 1e4:.2f} ha, {basis})")
    if pool is not None:
        P = gpd.GeoDataFrame({"note": ["standing water in a dry frame — never "
                                       "masked"]}, geometry=[pool], crs=OSGB)
        r = OUT / "W94_96_standing_water.geojson"
        P.to_file(r, driver="GeoJSON")
        saved(f"{r.name}  ({pool.area / 1e4:.3f} ha)")

    hollows = gpd.read_file(OUT / "W94_06_hollows.geojson").set_crs(
        OSGB, allow_override=True)
    hu = _valid(unary_union([_valid(x) for x in hollows.geometry]))
    inside = dark.intersection(hu).area / 1e4
    tot = dark.area / 1e4
    step(f"the bush mask is {tot:.2f} ha, {inside:.2f} ha of it inside a mapped "
         f"hollow and {tot - inside:.2f} ha outside one. The {inside:.2f} ha "
         f"inside a hollow is NOT lost: phase 8 restores it as wet wherever its "
         f"hollow reads wet and it sits at or below that water's level, and "
         f"leaves it dry otherwise. The {tot - inside:.2f} ha outside any "
         f"closed basin is excluded outright, having nowhere for water to stand")

    rows = []
    for f in sorted(OUT.glob("W94_08_flood_*.geojson")):
        if "_fixedz_" in f.name:
            continue
        d = f.stem.split("flood_")[1].replace("tiles_", "")
        if d in FALSE_WET_FRAMES:
            continue
        g = gpd.read_file(f).set_crs(OSGB, allow_override=True)
        u = _valid(unary_union([_valid(x) for x in g.geometry]))
        cor = _valid(u.difference(dark))
        rows.append({"read": f.stem.split("W94_08_flood_")[1], "date": d,
                     "cut_z": cut_z,
                     "read_ha": round(u.area / 1e4, 3),
                     "bush_overlap_ha": round(u.intersection(dark).area / 1e4, 3),
                     "corrected_ha": round(cor.area / 1e4, 3),
                     "corrected_ha_in_hollows": round(
                         cor.intersection(hu).area / 1e4, 3),
                     "removed_pct": round(100 * u.intersection(dark).area
                                          / u.area, 1)})
        r = rows[-1]
        info(f"  {r['read']:22s} {r['read_ha']:7.2f} ha -> "
             f"{r['corrected_ha']:7.2f} ha ({r['removed_pct']:5.1f} % bush), "
             f"{r['corrected_ha_in_hollows']:6.2f} ha of it in hollows")
    if rows:
        s = OUT / "W94_94_reads_corrected.csv"
        pd.DataFrame(rows).to_csv(s, index=False)
        saved(s.name)
    info("These rows are the RETROSPECTIVE correction of reads taken before the "
         "mask existed. Every read from here excludes the mask at source, in "
         "phase 8, and needs no correction at all.")
    return 0


if __name__ == "__main__":
    sys.exit(main())


