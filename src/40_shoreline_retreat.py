"""
40_shoreline_retreat.py — Shoreline retreat from the digitised coastline epochs
================================================================================

Wired into run_analysis.py 2026-08-29. Tier and execution mode are declared by
the orchestrator, not here; see outputs/pipeline_manifest.json for this script's
tier, execution mode, and current step index.

Purpose (one sentence)
    Measure shoreline displacement between the digitised coast lines as SIGNED
    shore-normal distance, with the diagnostics that decide whether the result
    is a measurement of a shoreline at all -- and WITHHOLD the rate when they
    say it is not.

Why this exists
    The retreat series lived in a working note as a session computation, so
    under D-006 nothing in it was citable. Making it a pipeline output is what
    D-060's Revisit-if asks for. But a retreat measurement that cannot
    distinguish a rigid shift of a digitised line from real retreat is not a
    measurement, so the diagnostics are not extras: they are what makes the
    rate mean anything.

The defect designed out
    The session computation used NEAREST DISTANCE from each sampled point to
    the other line. That quantity is ALWAYS POSITIVE. It structurally cannot
    see progradation, a sign change, or a floor -- which is exactly why a field
    with no progradation anywhere, whose least-eroding point sat at the highest
    independently surveyed rate on the frontage, read as a clean result.
    Signed shore-normal displacement makes the floor, the progradation count
    and the alongshore trend fall out for free. Nearest distance is retained as
    a labelled comparator column only, so the historical figures stay legible.

The gate (D-085)
    A "not citable" note relies on the next reader honouring it; a refusal does
    not, and D-006 makes a pipeline output citable BY DEFINITION. So the
    refusal is in the output, not beside it: rate_m_yr is written only when the
    floor, control and generalisation tests all pass, and is NA with a
    populated withheld_reason otherwise. The script does not fail the pipeline
    and does not warn-and-continue with a number. Nothing downstream can quote
    what is not there.

Reading order for anyone picking this up
    working/updates/NRG_script40_retreat_spec_2026-08-29.md   the signed-off spec
    working/updates/NRG_retreat_alongshore_probe_2026-08-29.md the measurements
    data/geo/GEO_PROVENANCE.md                                 the inputs
    D-085, D-086                                               the rulings
"""
from __future__ import annotations

__version__ = "1.11.0"  # Hollingham (2026) - 2026-11-25 (latest). Storm table gains ERA5 WAVES (data/waves/,
#   data/WAVES_PROVENANCE.md; hourly Hs, mean direction and peak period at 53.0 N 4.5 W, Caernarfon Bay): per event
#   day hs_max_m and the period / direction at that hour; per winter max_hs_m, its date, the record's 95th-percentile
#   daily Hs (hs_threshold_m, STORM_HS_PERCENTILE) and the days, and gale days, above it. BARMOUTH tides beside Holyhead
#   (paths.DATA_TIDES_BARMOUTH; own columns *_barmouth_m, never averaged); _read_bodc_holyhead -> _read_bodc. Every
#   new column is empty, with one warning, while its input is absent. Nothing in 40_01-40_08 moves. The BODC files
#   are read gzipped (*.txt.gz) as well as plain; 40_09 gains tide_days_holyhead / _barmouth (days with a clean level
#   in the winter), because BODC flags whole months improbable (Barmouth every value from 2016).
# 1.10.0  # Hollingham (2026) - 2026-11-25 (later; Martin, the 2009 question: "was there an unusually
#   large retreat between 2006 and 2009?"). coast2009.kml (20 April 2009 dune edge, traced 2026-10-23; GEO_PROVENANCE)
#   becomes an EPOCH: INTERVALS gain 2006-2009 and 2009-2017, measured on each pair's own extent and on the shared
#   modern frontage band, which 2009 spans at both ends, so the band does not move. The local projection origin stays
#   the centroid of the five ORIGIN_EPOCHS (the 2009 vertices are left out of it) and the generalisation bound stays
#   on the four modern lines, so no existing row of 40_01-40_07 moves. 40_02 gains, on the 2026 normals of the floor
#   interval, E/N (EPSG:27700), the ray to each earlier line (ray_2026_to_<epoch>_m) and the consecutive retreat on
#   those COMMON normals (common_<a>_<b>_m = ray_a - ray_b). 40_report_numbers gains retreat_2006_2009 / 2009_2017
#   medians (modern frontage) and the car-park stretch (CAR_PARK_WELL CEH15, DIPwells.kml "CAR PARK"; transects whose
#   2026 origin lies within CAR_PARK_RADIUS_M of the frontage point nearest it) per consecutive interval. 40_08 draws
#   the 2009 line.
#   STORM TABLE (Martin, same day): 40_09_storm_winters.csv (per July-June winter 2004/05-2022/23: days with an onshore
#   180-300 deg hourly mean >= 34 kt and >= 41 kt, event days >= 40 kt, the strongest onshore mean, largest 10-minute
#   gust, lowest MSL pressure), 40_10_storm_events.csv (every day with an onshore mean >= 40 kt) and 40_11_storm_winters.png
#   (with the shoreline epochs and Script 25's 2009 / 2014-15 well-drop windows), from the MIDAS Open Valley hourly
#   record read through utils.pet_alternatives.midas_hourly_wind (knots: wind_speed_unit_id 4, defined in each data
#   file's header). Holyhead tides (BODC processed 15-minute files in paths.DATA_TIDES_HOLYHEAD, data/TIDES_PROVENANCE.md)
#   fill the day's highest level, maximum surge (residual) and the winter's count of gale days above its 95th-percentile
#   daily high water when present; absent, those columns are written empty with one warning. storm_* report numbers.
# 1.9.0  # Hollingham (2026) - 2026-11-25 (Martin: "where's the map of the transects?"). New figure
#   40_08_transect_map.png: the digitised coastlines of 2006, 2017, 2021 and 2026, the shore-normal transects of
#   40_02 coloured by their signed 2006-2026 retreat, the mapped clay exposure (data/geo/clay.kml) and Script 38's
#   model-free transect wells (38_transect.csv: CEH22 coastal anchor ... NW4 inland anchor) joined as a line, over
#   add_kml_features / add_en_axes. Figure only; no CSV or report number changes.
# 1.8.0  # Hollingham (2026) - 2026-09-29. T-96 batch 2: 40_report_numbers.csv gains
#   shoreline_1899_georef_rmse_rate_m_per_yr = config.SHORELINE_1899_GEOREF_RMSE_M / the `years` of the
#   1899->2006 pair_extent interval (the value written to that row of 40_01_epoch_series.csv) - the
#   georeferencing error of the 1899 line expressed as a rate over that span (report8 SS3.7.4 "about
#   0.06 m/yr"). Additive; no existing output changes.
# 1.7.1  # Hollingham (2026) — 2026-09-28. T-91, per the signed-off spec
#   NRG_spec_T91_emits_2026-09-28: 40_report_numbers.csv now also carries the
#   modern_common_frontage 2006-2026 rate as a free-standing
#   `headline_retreat_rate_2006_2026_m_yr` row — the same headline the Methods
#   Supplement quotes as E_c and the downstream figures consume — instead of
#   only under a storm pair's context tag. Read from `modern_common` and the
#   gate result `ok` main() already has; NaN when the gate withholds it.
# 1.7.0  # Hollingham (2026) — 2026-09-27. The inland reference that orients
#   the transect normals seaward is the site outline's centroid (map_utils.
#   load_site_outline(), D-204, spec NRG_spec_site_outline_B), as _normals' docstring always said, not
#   the mean of every vertex of site_boundary.kml's 11,715 raster pieces.
# 1.6.3  # Hollingham (2026) — 2026-09-03. Creates DIR_40 in
#   main() rather than relying on paths.py doing it at import. No behavioural
#   change to the analysis. See paths.py 1.11.0 and task_register T-18.
# v1.6.2  # Hollingham (2026) — 2026-09-01. A SKIPPED STEP NO
#   LONGER DESTROYS ITS COMMITTED OUTPUT. `_dtm_profile` catches an ImportError,
#   warns, and returned an EMPTY FRAME — which `main()` then wrote over the good
#   committed file and announced as `Saved (0 rows)`. Measured 2026-09-01: with
#   rasterio absent, 40_05_dtm_profile.csv went from five rows to a bare header,
#   and the only symptom was a check_all failure pointing nowhere near the cause.
#   `git checkout` cannot undo it over the desktop bridge, where the mount refuses
#   the unlink.
#
#   THE DISTINCTION IS NOW EXPLICIT, and it is the fix: a DataFrame means the step
#   RAN (write it, zero rows included — "ran and found nothing" is a result);
#   None means it COULD NOT RUN (leave the committed file alone and say so).
#   `_write_or_preserve()` enforces it. THREE sites had the same shape, not one:
#   `_dtm_profile` on a missing library, `_coastal_sensitivity` on an unreadable
#   headline fit, and `_control` on a failed measurement. A stale artefact is the
#   lesser evil ON PURPOSE — it is visible to output_lag and to the console,
#   whereas an empty one looks like a measurement.
#
# v1.6.1  # Hollingham (2026) — 2026-09-01. ONE-LINE VALUE FIX.
#   The D-060 anchor row in 40_01_epoch_series.csv carried a hard-typed
#   `"years": 116.0` while _regression_test measures over 107.0. rate_m_yr is
#   computed, so it was right (0.645058 = 69.021/107); the row was internally
#   inconsistent and median/years returned 0.595. No document quotes either
#   span, so nothing had drifted into the corpus. Found 2026-09-01 by reading
#   the committed CSV, not by a gate: NOTHING CHECKS THAT rate_m_yr EQUALS
#   median_m / years WITHIN A ROW, and that check is worth adding.
#
# v1.6.0  # Hollingham (2026) — 2026-08-30. The instance tag
#   becomes `winter2019_20` (was `winter2019`, was `storm_pair_2019_20`), so all
#   twelve emitted parameter names change again: `winter2019_20_displacement_median_m`,
#   `winter2019_20_between_storm_expectation_m`, `winter2019_20_context_rate_m_yr`.
#   WHY, and it is the point of the change: `winter2019` was only unambiguous
#   under Martin's seasonal year (Spring-Summer-Autumn-Winter, named for its
#   start). Under config.MSL_HYDRO_YEAR_START_MONTH - van Willegen / Curreli
#   hydrology year B, 1 June to 31 May, named for its END, used by Scripts 11,
#   14, 25, 26, 32, 33 and 38 - the same winter is 2020. `winter2019_20` names
#   BOTH calendar years and so reads correctly under either convention, which is
#   what lets the three-place explanatory gloss come out. The gloss is REPLACED
#   by a plain statement of what the tag denotes (December 2019 to February
#   2020), not deleted: a reader still needs the months.
#   The tag SIDESTEPS the two-convention collision; it does not resolve it. Both
#   conventions remain in the corpus, untouched. See D-098's second 2026-08-30
#   note and work-register M30.
#
# v1.5.0  # Hollingham (2026) — 2026-08-30. The storm-pair
#   instance label becomes `winter2019` and every emitted parameter name carries
#   it, replacing `storm_pair_2019_20`. (Superseded by v1.6.0's `winter2019_20`;
#   the entry stands as the record of what v1.5.0 did.)
#   THE TAG NOW COMES FROM THE REGISTRY ROW, not from a literal inside
#   _report_numbers(): v1.4.0 hard-typed `tag = "storm_pair_2019_20"` there,
#   which is precisely the failure D-098's own Revisit-if anticipated for a
#   second pair - it would have silently emitted the first pair's parameter
#   names. _check_storm_tags() now refuses a duplicate or a malformed tag at
#   run time, so the collision cannot happen quietly. The tag is also emitted as
#   a column of 40_07_storm_pair.csv.
#   STORM_PAIRS keeps its name and 40_07_storm_pair.csv keeps its filename: the
#   registry is the CLASS (pairs bracketing a storm season) and the tag is one
#   INSTANCE of it. See the registry comment - do not "tidy" that split away.
#
# v1.4.0  # Hollingham (2026) — 2026-08-30. Adds the STORM
#   PAIR: two shorelines bracketing the 2019/20 winter storm season, measured on
#   the same estimator and the same projection origin as the epochs but held in
#   a SEPARATE registry (STORM_PAIRS) that feeds neither EPOCHS nor INTERVALS.
#   A 0.55-year interval in INTERVALS would enter the rate series AND move the
#   common-extent band every committed number is measured on, so the separation
#   is structural, not stylistic. NO RATE IS EMITTED for a storm pair - the
#   annualised figure is 16.2 m/yr and annualising one storm season is precisely
#   the error the coastal section warns against - so _measure's rate_m_yr,
#   min_rate_m_yr and years are dropped by an explicit key list and a runtime
#   assertion that none of them reaches the file. New outputs
#   40_07_storm_pair.csv and 40_report_numbers.csv; the storm displacement
#   travels with its two contexts (the repeat-tracing control p95 and the
#   between-storm expectation computed from the committed 2006-2026 rate).
#   The inputs were renamed brendan*.kml -> coast2019-09-11.kml /
#   coast2020-03-31.kml: the interval spans Brendan, Ciara and Dennis and cannot
#   separate them. See D-098.
#
# v1.3.0  # Hollingham (2026) — 2026-08-29. Emits the coastal
#   sensitivity delta_0/rate WITH the period match checked, closing the mismatch
#   in h0 = COAST_RETREAT_M * (delta_0 / COAST_RETREAT_RATE): delta_0 is fitted
#   over the whole record and the committed rate is a six-year window, so the
#   ratio was never a sensitivity. Measured, the fault is entirely in the
#   denominator - a window-matched delta_0 moves 0.5 %, the rate by 3.6x. The
#   window overlap is now computed and warned on every run rather than assumed.
#   New output 40_06_coastal_sensitivity.csv. See D-090.
#
# v1.2.0  # Hollingham (2026) — 2026-08-29. THE GATE OPENS. The
#   control is a BLIND repeat tracing of the 1/1/2006 imagery, which replaces the
#   fixed-feature test the spec first called for: two tracings of one image
#   cannot differ by real change, so their separation is this process's
#   digitising-plus-registration error - 2.34 m median, 5.53 m p95 across 130
#   normals. Tolerances set from that (6.0 m control, 5.0 m generalisation) and
#   all three tests now pass, so rate_m_yr is emitted and citable under D-006.
#   _control() verifies INDEPENDENCE first and refuses a tolerance-grade number
#   if the two tracings share any vertex - the previous attempt reused five and
#   read as excellent agreement. See D-089.
#
# v1.1.0  # Hollingham (2026) — 2026-08-29. Re-based on the
#   four-epoch series re-digitised in one sitting (2006 / 2017 / 2021 / 2026),
#   which carries its own control: the new 1/1/2006 line is the same imagery date
#   as the withdrawn one, and the pair measures digitising repeatability at
#   1.71 m median. DCoast_2015.kml deleted as unverifiable, so the D-060 anchor
#   is re-pointed at 1899 -> 2006 (0.645 m/yr against a published 0.65) and a
#   SECOND anchor added that depends on no historical file at all: a line
#   translated by a known distance must measure as that distance. The
#   no-progradation gate condition is dropped - it over-triggers on a long span
#   and the min-rate condition does the real work. See D-087.
#
# v1.0.0  # Hollingham (2026) — 2026-08-29. First issue, to the
#   signed-off spec. Signed shore-normal displacement; common frontage
#   restricted by EXTENT rather than hit-success (a spurious hit is a hit, and
#   a hit-success mask produced a phantom 22.8 m of southern progradation on
#   2026-08-29); a self-withholding headline; the fixed-feature control on the
#   identical code path; a measured chord-sagitta generalisation bound rather
#   than a densification that would only interpolate along the chords that are
#   the error; the DTM profile position that says WHICH INDICATOR these lines
#   are; and the D-060 regression test against the retained 2015 fixture.

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import math
import gzip
import re

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils import config, paths
from utils.console_utils import (banner, phase, step, info, warn, saved, note,
                                 result, done)
from utils.render_utils import render_figure
from utils.map_utils import load_site_outline, add_kml_features, add_en_axes
from pyproj import Transformer

SCRIPT_ID = "40"
VERSION = __version__

SPACING_M    = config.SHORE_NORMAL_SPACING_M
MAX_RANGE_M  = config.SHORE_NORMAL_MAX_RANGE_M
PUBLISHED_MAX = config.PUBLISHED_MAX_PROFILE_RATE
TOL_CONTROL  = config.SHORE_CONTROL_TOLERANCE_M
TOL_GENERAL  = config.SHORE_GENERALISATION_TOLERANCE_M

# Epoch registry. Dates are the imagery dates recorded in GEO_PROVENANCE.md;
# 1899 is the OS survey revision, not the printing. Nothing here is a magic
# number: each is the date the line depicts, and the intervals divide by the
# difference between them.
EPOCHS = [
    ("1899", paths.DATA_KML_COAST_1899, "1899-01-01"),
    ("2006", paths.DATA_KML_COAST_2006, "2006-01-01"),
    ("2009", paths.DATA_KML_COAST_2009, "2009-04-20"),   # 1.10.0: the 20 April 2009 imagery
    ("2017", paths.DATA_KML_COAST_2017, "2017-03-24"),
    ("2021", paths.DATA_KML_COAST_2021, "2021-04-04"),
    ("2026", paths.DATA_KML_COAST_2026, "2026-03-31"),
]

# The pairs reported. Consecutive intervals show the shape of the series; the
# two spans are what the documents would quote.
INTERVALS = [("1899", "2006"), ("2006", "2017"), ("2017", "2021"),
             ("2021", "2026"), ("2006", "2026"), ("1899", "2026"),
             ("2006", "2009"), ("2009", "2017")]          # 1.10.0: the 2009 split
# The intervals also measured on the shared modern frontage band. The band is
# the common extent of MODERN_BAND_EPOCHS only: 2009 spans it at both ends, so
# adding it would not move the band, and leaving it out says so by construction.
MODERN_BAND_EPOCHS = ("2006", "2017", "2021", "2026")
MODERN_INTERVALS = (("2006", "2017"), ("2017", "2021"), ("2021", "2026"),
                    ("2006", "2026"), ("2006", "2009"), ("2009", "2017"))
# The epochs whose vertices define the local projection origin: those of 1.9.0.
# A new epoch's vertices would shift the origin and move every committed number
# by a few centimetres for no reason, so 2009 is left out of it.
ORIGIN_EPOCHS = ("1899", "2006", "2017", "2021", "2026")
# Epochs measured on the COMMON 2026 normals in 40_02 (ray from each 2026 normal
# origin to the earlier line), so per-transect retreat can be compared across
# intervals on one set of transects.
COMMON_NORMAL_EPOCHS = ("2006", "2009", "2017", "2021")
# The beach car park: Martin recalls the January 2014 storm taking 10-15 m of
# dune there. Its position is CEH15's, which DIPwells.kml describes as "CAR
# PARK" (Features.kml's road, Line 23, ends a little beyond it). Transects whose
# 2026 normal origin lies within CAR_PARK_RADIUS_M of the frontage point nearest
# CEH15 are the car-park stretch.
CAR_PARK_WELL = "ceh15"
CAR_PARK_RADIUS_M = 250.0
FLOOR_INTERVAL = ("2006", "2026")   # longest modern interval; the floor test

# Storm pairs — (label, earlier path, earlier date, later path, later date).
#
# A SEPARATE REGISTRY, and the separation is the whole point (D-098). These two
# lines bracket a single winter, not an epoch of the shoreline series. Adding
# them to EPOCHS or INTERVALS would do two things this script must not do: put a
# 0.55-year interval into the rate series, where a reader meets it beside
# 2.32 m/yr and reads it as comparable; and enlarge the set whose _common_extent
# defines the modern frontage band, which would move every committed number
# measured on that band. Held here, the storm pair is measured on the same
# estimator, the same projection origin and the same cone mask as the epochs,
# and touches nothing else.
#
# The dates are the imagery dates in GEO_PROVENANCE.md, on the same footing as
# the EPOCHS dates above: each is the date the line depicts, and the interval is
# their difference. The label is deliberately the SEASON, not a storm. The
# interval contains Storm Brendan (13-14 January 2020) and Ciara and Dennis
# (February 2020); two frames five months apart cannot separate them, so naming
# the measurement for one of them would be a false attribution.
# CLASS AND INSTANCE - do not "tidy" this into one name. `STORM_PAIRS` is the
# CLASS: pairs of frames bracketing a storm season, measured as displacements.
# `winter2019_20` is one INSTANCE of that class. Renaming the registry (or
# 40_07_storm_pair.csv) to "winter" would lose the reason the registry exists,
# and renaming the instance to "storm_pair" would lose which winter it is.
#
# Row fields, in order:
#   tag           machine identity. It is the prefix of EVERY parameter name
#                 this pair emits, and it is READ FROM HERE - never re-typed in
#                 _report_numbers(). See _check_storm_tags().
#   label         prose, for the console and for figure text. Editing it is
#                 cosmetic BY DESIGN: deriving the tag by slugifying this string
#                 would mean a wording change silently renamed published
#                 parameters, which is a worse bug than the one being fixed.
#   earlier path, earlier date, later path, later date.
#
# WHAT THE TAG DENOTES. `winter2019_20` is the winter of December 2019 to
# February 2020 - the winter the two frames bracket. It names both calendar
# years deliberately, so it reads correctly whether the reader numbers a year
# from its start or from its finish, and therefore needs no convention gloss to
# be unambiguous. (It replaced `winter2019`, which was correct only under a year
# numbered from its start; see D-098.)
STORM_PAIRS = [
    ("winter2019_20", "2019/20 winter storm sequence",
     paths.DATA_KML_COAST_2019_09_11, "2019-09-11",
     paths.DATA_KML_COAST_2020_03_31, "2020-03-31"),
]


def _check_storm_tags():
    """No two pairs may share a tag, and a tag must be usable as a name prefix.

    This is the check that makes the registry-derived tag worth having. Deriving
    it rather than typing it stops one pair borrowing another's parameter names
    by omission; this stops it by collision. Both are the same defect - two pairs
    emitting `winter2019_20_displacement_median_m` - arriving by different routes.
    """
    tags = [row[0] for row in STORM_PAIRS]
    dupes = sorted({x for x in tags if tags.count(x) > 1})
    if dupes:
        raise RuntimeError(
            f"STORM_PAIRS tags are not unique: {dupes}. Every parameter name a "
            f"pair emits is prefixed with its tag, so two pairs sharing one "
            f"would overwrite each other in 40_report_numbers.csv")
    bad = [x for x in tags if not re.fullmatch(r"[a-z][a-z0-9_]*", x)]
    if bad:
        raise RuntimeError(
            f"STORM_PAIRS tags must be lowercase identifiers: {bad}. The tag is "
            f"a parameter-name prefix, not prose - the prose is the label field")

# The interval whose MEASURED rate supplies the between-storm expectation — what
# this frontage would have moved over the storm interval at its long-run pace.
# It is read from the measurement made in this same run, never typed: the
# expectation has to move when the rate does, or it becomes a stale comparator
# that flatters the storm result.
STORM_CONTEXT_INTERVAL = FLOOR_INTERVAL

# Keys _measure returns that MUST NOT reach a storm-pair row. rate_m_yr for the
# pair is 16.2 m/yr, which is arithmetic, not a rate of shoreline change; years
# is 0.55 and invites the division. The row is therefore built from an explicit
# key list and this set is asserted absent before the frame is written, because
# an output list is exactly the mechanism that has silently dropped a wanted
# column before and the same mechanism has to be checked when it is dropping one
# deliberately.
STORM_FORBIDDEN_KEYS = ("rate_m_yr", "min_rate_m_yr", "years")

# The fields a storm-pair row DOES carry. Displacement and the interval in days.
STORM_KEEP_KEYS = ("n", "median_m", "p10_m", "p90_m", "min_m", "max_m",
                   "n_progradation", "alongshore_slope_m_per_km",
                   "alongshore_r", "frontage_span_m",
                   "frontage_lo_local_m", "frontage_hi_local_m",
                   "nearest_median_m")

# D-060's published long-run rate, the external anchor. It was originally
# computed against DCoast_2015.kml, which was DELETED on 2026-08-29 as
# unverifiable. The anchor survived the deletion: the same 1899 dune edge
# measured against the 2006 line of the re-digitised series returns 0.645 m/yr
# over 107 years, so the published figure is reproduced by a route whose every
# input has known provenance. RATES are compared, not displacements, because the
# endpoints now differ.
D060_RATE_M_YR     = 0.65
D060_TOLERANCE_PCT = 10.0

# Second anchor, independent of every historical file: a line translated by a
# known distance must measure as that distance. It tests the ESTIMATOR rather
# than agreement with a past computation, so it cannot rot when an input is
# withdrawn -- which is exactly what happened to the first one.
SYNTHETIC_OFFSET_M    = 37.5
# Not exact, and the reason is geometric rather than sloppy: a RIGID translation
# of a curved line is not a constant shore-normal offset along it, so the median
# recovers the translation to about a percent. The tolerance is set to catch a
# sign error or a broken estimator, which is what it is for, not to certify
# sub-metre accuracy.
SYNTHETIC_TOLERANCE_M = 1.0

# Days in a Julian year. Not a scientific parameter: it is the unit conversion
# already used to turn an epoch date difference into `years` in main(), named
# here so the storm pair's expectation uses the same one rather than a second
# copy of the literal.
DAYS_PER_YEAR = 365.25


# ======================================================================
# Geometry
# ======================================================================
def _read_kml(path):
    """Every <coordinates> block in a KML, as arrays of (lon, lat)."""
    raw = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    out = []
    for block in re.findall(r"<coordinates>(.*?)</coordinates>", raw, re.S):
        pts = []
        for tok in block.split():
            parts = tok.split(",")
            if len(parts) >= 2:
                pts.append((float(parts[0]), float(parts[1])))
        if len(pts) >= 2:
            out.append(np.asarray(pts, dtype=float))
    if not out:
        raise ValueError(f"no usable <coordinates> in {path}")
    return out


_ORIGIN = (0.0, 0.0)   # set in main() once every input is loaded


def _projection_origin(all_lonlat):
    """Centroid of every input vertex — the local projection origin."""
    stacked = np.vstack(all_lonlat)
    return float(stacked[:, 1].mean()), float(stacked[:, 0].mean())


def _to_local_m(lonlat, lat0, lon0):
    """Local equirectangular metres about (lat0, lon0).

    Over ~4 km at 53 deg N the distortion is far below the 5.95 m
    georeferencing error carried by the 1899 line. Asserted in main(), not
    assumed.
    """
    r = 6371000.0
    x = np.radians(lonlat[:, 0] - lon0) * r * math.cos(math.radians(lat0))
    y = np.radians(lonlat[:, 1] - lat0) * r
    return np.column_stack([x, y])


def _resample(P, spacing):
    """Points every `spacing` metres along polyline P, with arc length."""
    seg = np.hypot(*(P[1:] - P[:-1]).T)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    n = max(int(s[-1] // spacing), 1)
    t = np.linspace(0.0, s[-1], n + 1)
    return np.column_stack([np.interp(t, s, P[:, 0]),
                            np.interp(t, s, P[:, 1])]), t


def _normals(P, inland_xy):
    """Unit normals oriented SEAWARD, i.e. away from the inland reference.

    The reference is the centroid of the site-boundary mask, not a hardcoded
    bearing: a bearing baked in here would silently mis-sign the whole field if
    the frontage were ever re-digitised over a different stretch.
    """
    d = np.gradient(P, axis=0)
    T = d / np.hypot(*d.T)[:, None]
    N = np.column_stack([-T[:, 1], T[:, 0]])
    outward = P - inland_xy
    N[np.einsum("ij,ij->i", N, outward) < 0] *= -1.0
    return N


def _bearings_deg(N):
    return (np.degrees(np.arctan2(N[:, 0], N[:, 1])) + 360.0) % 360.0


def _cone_mask(N, half_angle_deg=90.0):
    """Normals within `half_angle_deg` of the frontage's mean seaward direction.

    A near-duplicate or doubled-back vertex makes the local tangent degenerate
    and can flip a normal by ~180 degrees. One such normal contributes a
    sign-flipped displacement to the median, so they are EXCLUDED rather than
    trusted -- and counted, because a frontage where many fall outside the cone
    is one this method should not be measuring at all.

    The mean direction is a circular mean, not an average of bearings: bearings
    near 0/360 average to nonsense.
    """
    mean = N.mean(axis=0)
    mean = mean / float(np.hypot(*mean))
    cos_lim = math.cos(math.radians(half_angle_deg))
    return (N @ mean) >= cos_lim, mean


def _ray_signed(p, n, Q, max_range):
    """Signed distance from p to polyline Q along +/- n. Positive = seaward.

    No intersection within max_range is NaN, never zero: a zero would read as
    "no movement" and quietly enter a median.
    """
    A, B = Q[:-1], Q[1:]
    AB = B - A
    den = AB[:, 0] * (-n[1]) - AB[:, 1] * (-n[0])
    ok = np.abs(den) > 1e-12
    AP = p - A
    safe = np.where(ok, den, 1.0)
    u = np.where(ok, (AP[:, 0] * (-n[1]) - AP[:, 1] * (-n[0])) / safe, np.nan)
    s = np.where(ok, (AB[:, 0] * AP[:, 1] - AB[:, 1] * AP[:, 0]) / safe, np.nan)
    hit = ok & (u >= 0.0) & (u <= 1.0) & (np.abs(s) <= max_range)
    if not hit.any():
        return float("nan")
    cand = s[hit]
    return float(cand[np.argmin(np.abs(cand))])


def _nearest_signed(p, n, Q):
    """Superseded comparator: nearest distance, signed by the normal.

    Retained so the historical figures stay comparable. Its magnitude is
    always the minimum distance, so it cannot see a floor -- which is the
    defect this script exists to remove, kept visible rather than deleted.
    """
    A, B = Q[:-1], Q[1:]
    AB = B - A
    denom = np.einsum("ij,ij->i", AB, AB)
    denom = np.where(denom > 0, denom, 1.0)
    t = np.clip(np.einsum("ij,ij->i", p - A, AB) / denom, 0.0, 1.0)
    proj = A + t[:, None] * AB
    dist = np.hypot(*(proj - p).T)
    i = int(np.argmin(dist))
    return float(dist[i] * np.sign(np.dot(proj[i] - p, n)))


# ======================================================================
# Measurement
# ======================================================================
def _identify_1899_lines(lines_m, ref_2020, inland_xy):
    """Which placemark of coast1899.kml is the dune edge?

    CORRECTION 2026-08-29: an earlier version of this docstring said the file
    "labels neither" line. It does. Its <description> names them (id=1
    High_tide, id=2 Dune_edge, mean separation 124 m) and each placemark
    carries a High_tide / Dune_edge SimpleData flag. The claim was false and is
    withdrawn.

    The measurement check is kept anyway, for a better reason than the one
    given: it does not depend on the labels being preserved. A re-export, a
    reorder, or a rebuild of the file that dropped the SimpleData would swap the
    high-water line for the dune edge and take every long-run rate with it, and
    nothing downstream would notice. Each candidate is measured against the 2020
    line and the SMALLER displacement is the dune edge, the high-water mark
    lying further seaward by construction. The labels and the measurement agree
    today; the point is that the script does not need them to.
    """
    S, _ = _resample(ref_2020, SPACING_M)
    N = _normals(S, inland_xy)
    meds = []
    for cand in lines_m:
        d = np.array([_ray_signed(S[k], N[k], cand, 600.0) for k in range(len(S))])
        d = d[~np.isnan(d)]
        meds.append(float(np.median(d)) if len(d) else float("inf"))
    edge = int(np.argmin(meds))
    hwm = 1 - edge if len(lines_m) == 2 else None
    return edge, hwm, meds


def _common_extent(lines_m, spacing):
    """Northing band spanned by EVERY line, minus one spacing at each end.

    Restricted by EXTENT, not by hit-success, and the difference is not
    cosmetic. coast2012 runs ~400 m further south than the other two; normals
    in that gap strike its unmatched southern tail and DO return a hit. A
    hit-success mask keeps those, and on 2026-08-29 that produced a reported
    22.8 m of southern progradation that does not exist.
    """
    lo = max(float(P[:, 1].min()) for P in lines_m) + spacing
    hi = min(float(P[:, 1].max()) for P in lines_m) - spacing
    return lo, hi


def _measure(earlier, later, years, inland_xy, keep_lo=None, keep_hi=None):
    """Signed shore-normal displacement from `later` back to `earlier`.

    keep_lo/keep_hi None means UNRESTRICTED — every normal that finds an
    intersection. That basis is not a shortcut: it is what the D-060 regression
    test needs, because imposing this project's masking on a historical result
    and then calling the difference a failure compares two different quantities.
    """
    S, arc = _resample(later, SPACING_M)
    N = _normals(S, inland_xy)
    good, _ = _cone_mask(N)
    within = (np.ones(len(S), dtype=bool) if keep_lo is None
              else (S[:, 1] >= keep_lo) & (S[:, 1] <= keep_hi))
    within = within & good
    ray = np.full(len(S), np.nan)
    near = np.full(len(S), np.nan)
    for k in np.where(within)[0]:
        ray[k] = _ray_signed(S[k], N[k], earlier, MAX_RANGE_M)
        near[k] = _nearest_signed(S[k], N[k], earlier)
    ok = ~np.isnan(ray)
    v = ray[ok]
    if len(v) == 0:
        return None
    slope, intercept = (np.polyfit(arc[ok] / 1000.0, v, 1) if len(v) > 2
                        else (np.nan, np.nan))
    r = (float(np.corrcoef(arc[ok] / 1000.0, v)[0, 1]) if len(v) > 2
         else float("nan"))
    return {
        "n": int(ok.sum()),
        "median_m": float(np.median(v)),
        "min_m": float(v.min()), "max_m": float(v.max()),
        "p10_m": float(np.percentile(v, 10)),
        "p90_m": float(np.percentile(v, 90)),
        "n_progradation": int((v < 0).sum()),
        "alongshore_slope_m_per_km": float(slope),
        "alongshore_r": r,
        "frontage_span_m": float(arc[ok].max() - arc[ok].min()),
        "frontage_lo_local_m": (float("nan") if keep_lo is None else float(keep_lo)),
        "frontage_hi_local_m": (float("nan") if keep_hi is None else float(keep_hi)),
        "years": years,
        "rate_m_yr": float(np.median(v)) / years,
        "min_rate_m_yr": float(v.min()) / years,
        "nearest_median_m": float(np.nanmedian(near[ok])),
        "_arc": arc, "_ray": ray, "_near": near, "_S": S, "_N": N, "_ok": ok,
    }


# ======================================================================
# Diagnostics
# ======================================================================
def _generalisation_bound(lines_m, names):
    """Chord-sagitta bound from differencing polylines of unequal density.

    The script does NOT densify. Resampling a 14-vertex line interpolates along
    the very chords that are the error and adds no accuracy. It measures the
    bound instead: at each vertex of the finer line, the offset from the chord
    joining the neighbours a coarse-spacing away.
    """
    rows = []
    spacings = {}
    for nm, P in zip(names, lines_m):
        seg = np.hypot(*(P[1:] - P[:-1]).T)
        spacings[nm] = float(np.median(seg)) if len(seg) else float("nan")
    coarse = max(spacings.values())
    for nm, P in zip(names, lines_m):
        S, arc = _resample(P, SPACING_M)
        sag = []
        for k in range(len(S)):
            lo = np.searchsorted(arc, arc[k] - coarse / 2.0)
            hi = np.searchsorted(arc, arc[k] + coarse / 2.0) - 1
            if lo < 0 or hi >= len(S) or hi - lo < 2:
                continue
            a, b, p = S[lo], S[hi], S[k]
            ab = b - a
            L = float(np.hypot(*ab))
            if L <= 0:
                continue
            ap = p - a
            sag.append(abs(float(ab[0] * ap[1] - ab[1] * ap[0])) / L)
        rows.append({
            "line": nm, "vertices": int(len(P)),
            "median_vertex_spacing_m": spacings[nm],
            "coarsest_spacing_m": coarse,
            "sagitta_median_m": float(np.median(sag)) if sag else float("nan"),
            "sagitta_p90_m": float(np.percentile(sag, 90)) if sag else float("nan"),
            "sagitta_max_m": float(np.max(sag)) if sag else float("nan"),
        })
    bound = float(np.nanmax([r["sagitta_p90_m"] for r in rows]))
    return pd.DataFrame(rows), bound


def _control(line_2006, inland_xy):
    """The repeat-tracing control: one image traced twice, independently.

    Two tracings of the SAME imagery cannot differ by real shoreline change, so
    their separation is the digitising-plus-registration error of this process,
    measured rather than assumed.

    It replaces the fixed-feature control the spec first called for. Martin ruled
    against holding out for that, and this is arguably the better test anyway: a
    fixed feature isolates registration, while what actually threatens the
    measurement is the whole process - registration AND where the operator judges
    the dune edge to be.

    INDEPENDENCE IS THE WHOLE POINT AND IS CHECKED HERE. The first attempt at
    this control was traced with the earlier line loaded and reused five of its
    vertices; the resulting 1.71 m looked like excellent agreement and was
    partly agreement of a line with itself. If any vertex is shared, this refuses
    to report a tolerance-grade number.
    """
    path = paths.DATA_KML_COAST_2006_REPEAT
    if not path.exists():
        return pd.DataFrame(columns=["pair", "n", "median_abs_m", "p95_abs_m"]), None
    repeat = _to_local_m(_read_kml(path)[0], *_ORIGIN)

    shared = ({tuple(np.round(p, 9)) for p in line_2006}
              & {tuple(np.round(p, 9)) for p in repeat})
    if shared:
        warn(f"control REJECTED: the two tracings share {len(shared)} vertices to "
             f"1e-9 — they are not independent, and a tolerance set from them "
             f"would calibrate the gate against itself")
        return pd.DataFrame([{"pair": "2006 vs 2006_blind", "n": 0,
                              "median_abs_m": float("nan"),
                              "p95_abs_m": float("nan"),
                              "shared_vertices": len(shared)}]), None

    lo, hi = _common_extent([line_2006, repeat], SPACING_M)
    m = _measure(line_2006, repeat, 1.0, inland_xy, lo, hi)
    if m is None:
        return None, None                # skipped, NOT empty: see _write_or_preserve
    a = np.abs(m["_ray"][m["_ok"]])
    row = {"pair": "coast2006 vs coast2006B_blind", "n": int(len(a)),
           "shared_vertices": 0,
           "median_abs_m": float(np.median(a)),
           "p90_abs_m": float(np.percentile(a, 90)),
           "p95_abs_m": float(np.percentile(a, 95)),
           "max_abs_m": float(a.max()),
           "signed_median_m": float(np.median(m["_ray"][m["_ok"]]))}
    return pd.DataFrame([row]), row["p95_abs_m"]


def _write_or_preserve(df, path, what: str) -> None:
    """Write a result, or LEAVE A COMMITTED ARTEFACT ALONE when the step was skipped.

    The distinction this draws is the whole point of the function, and getting
    it wrong destroyed data on 2026-09-01:

      df is a DataFrame  -- the step RAN. Write it, even with zero rows: "the
                            step ran and found nothing" is a result and the
                            committed file should say so.
      df is None         -- the step COULD NOT RUN, because a library is missing
                            or an input was unreadable. That is not a result. The
                            previous file is left exactly as it stands and the
                            skip is reported.

    Before this existed, a skipped step returned an empty frame that was written
    unconditionally, so a missing optional dependency silently replaced a good
    committed output with a header-only file and announced it as `Saved (0
    rows)`. The only symptom was a check_all failure pointing nowhere near the
    cause, and `git checkout` cannot undo it over the desktop bridge, where the
    mount refuses the unlink.

    Leaving the file stale is the lesser evil ON PURPOSE. A stale artefact is
    visible to `output_lag` and to anyone reading the console; an empty one
    looks like a measurement.
    """
    if df is None:
        warn(f"{path.name} NOT written — the step was skipped, so the committed "
             f"file is left as it stands. Re-run where the step can run before "
             f"trusting it.")
        return
    df.to_csv(path, index=False)
    saved(path.name, what.format(n=len(df)))


def _dtm_profile(measured, lat0, lon0):
    """Where each line sits on the LiDAR DTM — WHICH INDICATOR these lines are.

    One surface postdates every line, so this CANNOT separate real retreat from
    indicator drift inside the series: a retreating dune reproduces the
    elevation signature of drift, and an ordering by age is what retreat
    predicts anyway. What it does establish is the comparison against an
    external dune-toe survey, because the newest line and the surface are close
    enough in date for that one reading to mean something.
    """
    try:
        import rasterio
        from pyproj import Transformer
    except Exception as exc:                                   # pragma: no cover
        warn(f"DTM profile skipped — {exc}")
        return None                      # skipped, NOT empty: see _write_or_preserve
    src = rasterio.open(paths.DATA_DEM)
    band = src.read(1).astype(float)
    inv = ~src.transform
    tr = Transformer.from_crs("EPSG:4326", str(src.crs), always_xy=True)
    r = 6371000.0

    def to_bng(xy):
        lon = lon0 + np.degrees(xy[:, 0] / (r * math.cos(math.radians(lat0))))
        lat = lat0 + np.degrees(xy[:, 1] / r)
        e, n = tr.transform(lon, lat)
        return np.column_stack([e, n])

    def z_at(xy):
        bng = to_bng(xy)
        col, row = inv * (bng[:, 0], bng[:, 1])
        row = np.clip(np.nan_to_num(np.asarray(row), nan=0).astype(int), 0, band.shape[0] - 1)
        col = np.clip(np.nan_to_num(np.asarray(col), nan=0).astype(int), 0, band.shape[1] - 1)
        return band[row, col]

    S, N, ok = measured["_S"], measured["_N"], measured["_ok"]
    rows = [{"line": "coast2026", "elevation_median_m_aod": float(np.median(z_at(S)[ok]))}]
    offs = np.arange(0.0, 260.0, 2.0)
    prof = np.stack([z_at(S + o * N) for o in offs], axis=1)
    for thr in (0.5, 2.0, 3.0, 4.0):
        hits = []
        for k in np.where(ok)[0]:
            below = np.where(prof[k] <= thr)[0]
            hits.append(offs[below[0]] if len(below) else np.nan)
        h = np.array(hits, dtype=float)
        rows.append({"line": "coast2026",
                     "contour_m_aod": thr,
                     "seaward_distance_median_m": float(np.nanmedian(h))})
    return pd.DataFrame(rows)


def _coastal_sensitivity(measured, epoch_date):
    """delta_0 / retreat_rate — and the period match that makes it meaningful.

    THE DEFECT THIS FIXES. Scripts 20 and 09f build the single-event edge
    drawdown as

        h0 = COAST_RETREAT_M * (delta_0 / COAST_RETREAT_RATE)

    where delta_0 is fitted over the WHOLE record (2005-03 to 2026-02) and the
    committed COAST_RETREAT_RATE = 8.3 m/yr is a SIX-YEAR window (2014-2020).
    The ratio asserts "the water table fell delta_0 per year while the shore
    retreated R per year, so this much head per metre of retreat" - which is only
    a sensitivity if both describe the same period. They did not.

    Measured 2026-08-29, the mismatch is entirely in the denominator: refitting
    delta_0 on a window matched to the retreat epochs moves it 0.5 % (31.328 ->
    31.481 mm/yr), while the rate moves by a factor of 3.6 (8.3 -> 2.321). So the
    numerator was never the problem.

    This emits the matched sensitivity and, more importantly, the OVERLAP between
    the two windows, so the match is checked on every run rather than asserted
    once in a comment.
    """
    rows = []
    try:
        head = pd.read_csv(paths.OUT_25_FIT_PARAMETERS)
        hrow = head[(head["source"] == "forest_free") & (head["model"] == "linear_capped")]
        d0_head = abs(float(hrow["delta_0_mm_yr"].iloc[0])) if len(hrow) else float("nan")
    except Exception as exc:
        warn(f"coastal sensitivity: headline fit unreadable ({exc})")
        return None                      # skipped, NOT empty: see _write_or_preserve

    d0_match, w_start, w_end = float("nan"), None, None
    try:
        sweep = pd.read_csv(paths.OUT_25_WINDOW_SWEEP)
        # the sweep row whose window START is closest to the retreat window start
        target = epoch_date["2006"]
        sweep["_s"] = pd.to_datetime(sweep["window_start"] + "-01")
        pick = sweep.iloc[(sweep["_s"] - target).abs().argmin()]
        d0_match = abs(float(pick["delta_0_mm_yr"]))
        w_start, w_end = pick["window_start"], pick["window_end"]
    except Exception as exc:
        warn(f"coastal sensitivity: window sweep unreadable ({exc}) — "
             f"matched delta_0 unavailable")

    m = measured.get(FLOOR_INTERVAL)
    if m is None:
        return pd.DataFrame()
    r_start, r_end = epoch_date[FLOOR_INTERVAL[0]], epoch_date[FLOOR_INTERVAL[1]]

    overlap = float("nan")
    if w_start is not None:
        ws, we = pd.Timestamp(w_start + "-01"), pd.Timestamp(w_end + "-01")
        lo, hi = max(ws, r_start), min(we, r_end)
        span = max((we - ws).days, (r_end - r_start).days)
        overlap = max((hi - lo).days, 0) / span if span else float("nan")

    rate = m["rate_m_yr"]
    for label, d0, note in (("headline", d0_head, "Script 25 forest-free linear_capped, whole record"),
                            ("window_matched", d0_match,
                             f"Script 25 window sweep, {w_start} to {w_end}")):
        if d0 != d0:
            continue
        rows.append({
            "delta0_basis": label, "delta0_mm_yr": d0,
            "delta0_window_start": w_start if label == "window_matched" else "2005-03",
            "delta0_window_end": w_end if label == "window_matched" else "2026-02",
            "retreat_interval": f"{FLOOR_INTERVAL[0]}-{FLOOR_INTERVAL[1]}",
            "retreat_rate_m_yr": rate,
            "retreat_years": m["years"],
            "window_overlap_fraction": overlap,
            "sensitivity_mm_per_m": d0 / rate,
            "h0_single_event_mm": config.COAST_RETREAT_M * d0 / rate,
            "note": note,
        })
    # and the committed constant, for the comparison the documents need
    rows.append({
        "delta0_basis": "headline", "delta0_mm_yr": d0_head,
        "delta0_window_start": "2005-03", "delta0_window_end": "2026-02",
        "retreat_interval": "config COAST_RETREAT_RATE (2014-2020)",
        "retreat_rate_m_yr": config.COAST_RETREAT_RATE,
        "retreat_years": 6.0, "window_overlap_fraction": float("nan"),
        "sensitivity_mm_per_m": d0_head / config.COAST_RETREAT_RATE,
        "h0_single_event_mm": config.COAST_RETREAT_M * d0_head / config.COAST_RETREAT_RATE,
        "note": "THE COMMITTED CONSTRUCTION — periods do NOT match; kept for comparison",
    })
    df = pd.DataFrame(rows)

    if overlap == overlap and overlap < 0.9:
        warn(f"delta_0 and the retreat rate overlap on only {overlap:.0%} of their "
             f"windows — the ratio is not a sensitivity at that overlap")
    else:
        info(f"period match: delta_0 {w_start}–{w_end} against retreat "
             f"{FLOOR_INTERVAL[0]}–{FLOOR_INTERVAL[1]}, overlap {overlap:.0%}")
    mm = df[df.delta0_basis == "window_matched"]
    if len(mm):
        r = mm.iloc[0]
        info(f"matched sensitivity {r['sensitivity_mm_per_m']:.3f} mm per m of "
             f"retreat -> h0 = {r['h0_single_event_mm']:.2f} mm for a "
             f"{config.COAST_RETREAT_M:.0f} m event "
             f"(committed construction gives {df.iloc[-1]['h0_single_event_mm']:.2f} mm)")
    return df


def _storm_pair(inland_xy, control_p95_m, context):
    """Shore-normal displacement across a storm season — a DISPLACEMENT, no rate.

    Same estimator, same projection origin, same cone mask and the same
    pair-extent basis as an epoch interval. What differs is what comes out: an
    epoch interval is quoted as a rate because two decades of shoreline change
    average to one, and a single winter does not. Dividing 8.9 m by 0.55 yr
    gives 16.2 m/yr, a number with the units of a rate and the meaning of an
    arithmetic accident, and the coastal section exists partly to warn against
    exactly that step. So the rate is not withheld-with-a-reason here as the
    D-085 headline is; it is never formed.

    Two contexts travel in the same row, because the displacement alone does not
    say whether it is a measurement:

      control_p95_m -- the repeat-tracing control, measured this run by
          _control(). Tracing error scatters about zero, so it bounds what a
          digitising artefact could produce.
      expected_m    -- what this frontage moves over the SAME number of days at
          the measured long-run rate, computed from the interval in `context`.
          Never typed: a comparator frozen at the moment someone read it would
          flatter this result the moment the rate moved.
    """
    ctx_rate, ctx_label, ctx_years = context
    _check_storm_tags()
    rows = []
    for tag, label, e_path, e_date, l_path, l_date in STORM_PAIRS:
        earlier = _to_local_m(_read_kml(e_path)[0], *_ORIGIN)
        later = _to_local_m(_read_kml(l_path)[0], *_ORIGIN)
        t0, t1 = pd.Timestamp(e_date), pd.Timestamp(l_date)
        days = int((t1 - t0).days)
        lo, hi = _common_extent([earlier, later], SPACING_M)
        # years=1.0 is passed only because _measure's signature requires it. The
        # rate fields it computes from it are discarded below and never reach
        # the file; nothing here divides by an interval.
        m = _measure(earlier, later, 1.0, inland_xy, lo, hi)
        if m is None:
            warn(f"storm pair {label}: no measurable normals")
            continue
        # `tag` is carried into the emitted file so the CSV and the parameter
        # names in 40_report_numbers.csv can be tied together without knowing
        # the registry.
        row = {"tag": tag, "label": label,
               "earlier_file": pathlib.Path(e_path).name,
               "later_file": pathlib.Path(l_path).name,
               "earlier_date": e_date, "later_date": l_date,
               "interval_days": days}
        row.update({k: m[k] for k in STORM_KEEP_KEYS})
        row["control_p95_m"] = control_p95_m
        row["expected_m"] = (float("nan") if ctx_rate != ctx_rate
                             else ctx_rate * days / DAYS_PER_YEAR)
        row["expected_basis"] = ctx_label
        row["estimator"] = "signed_shore_normal_ray"
        row["basis"] = "pair_extent"
        row["rate_emitted"] = False
        row["rate_note"] = ("displacement only — a single storm season is not "
                            "annualised (D-098)")
        leaked = sorted(set(row) & set(STORM_FORBIDDEN_KEYS))
        if leaked:
            raise RuntimeError(f"storm-pair row carries {leaked}; a storm pair "
                               f"must not emit an annualised rate (D-098)")
        rows.append(row)
        step(f"{label}: median {row['median_m']:.3f} m over {days} days "
             f"(n={row['n']}, progradation {row['n_progradation']}, "
             f"min {row['min_m']:.3f} m)")
        info(f"    against a repeat-tracing control p95 of "
             f"{control_p95_m if control_p95_m is None else f'{control_p95_m:.3f}'} m "
             f"and a between-storm expectation of {row['expected_m']:.3f} m "
             f"over the same {days} days at the {ctx_label} rate "
             f"({ctx_rate:.4f} m/yr over {ctx_years:.2f} yr)")
    return pd.DataFrame(rows)


def _report_numbers(storm_df, context):
    """The citable storm-pair values, so displacement and context travel together.

    Every value is read out of the frame this run produced. Nothing is retyped.
    """
    ctx_rate, ctx_label, ctx_years = context
    rows = []
    for _, r in storm_df.iterrows():
        era = f"{r['earlier_date']} to {r['later_date']}"
        # THE TAG COMES FROM THE ROW, which came from the registry. v1.4.0 typed
        # a literal here, and a second pair would then have emitted the FIRST
        # pair's parameter names into this same file - silently, because nothing
        # about a duplicated Parameter string looks wrong. D-098's Revisit-if
        # named this exact case; _check_storm_tags() now also refuses duplicates
        # at source.
        tag = r["tag"]
        # A plain statement of what the tag denotes, not a convention gloss:
        # `winter2019_20` names both calendar years, so it does not depend on
        # which end of a year the reader numbers from. The gloss v1.5.0 carried
        # here was load-bearing only while the tag was `winter2019`.
        season_note = ("the winter of December 2019 to February 2020, which "
                       "these two frames bracket")
        pairs = [
            (f"{tag}_displacement_median_m", r["median_m"], "m",
             "median signed shore-normal displacement, positive = retreat; "
             "NOT annualised — see 40_07_storm_pair.csv. Covers " + season_note),
            (f"{tag}_interval_days", r["interval_days"], "days",
             "imagery dates, inclusive difference"),
            (f"{tag}_n_normals", r["n"], "count",
             "normals returning an intersection on the pair extent"),
            (f"{tag}_n_progradation", r["n_progradation"], "count",
             "normals moving seaward; tracing error scatters about zero, so an "
             "all-positive field is the evidence this is not a digitising artefact"),
            (f"{tag}_displacement_min_m", r["min_m"], "m",
             "least-retreating normal on the frontage"),
            (f"{tag}_displacement_p10_m", r["p10_m"], "m", "10th percentile"),
            (f"{tag}_displacement_p90_m", r["p90_m"], "m", "90th percentile"),
            (f"{tag}_displacement_max_m", r["max_m"], "m",
             "most-retreating normal on the frontage"),
            (f"{tag}_frontage_span_m", r["frontage_span_m"], "m",
             "alongshore span measured"),
            (f"{tag}_control_p95_m", r["control_p95_m"], "m",
             "repeat-tracing control p95 from 40_03_control.csv, measured this "
             "run; the 1/1/2006 imagery traced twice, blind"),
            (f"{tag}_between_storm_expectation_m", r["expected_m"], "m",
             f"what this frontage moves over the same {int(r['interval_days'])} "
             f"days at the measured {ctx_label} rate — computed, not typed"),
            (f"{tag}_context_rate_m_yr", ctx_rate, "m/yr",
             f"the long-run rate the expectation is built from, measured over "
             f"{ctx_years:.4f} yr ({ctx_label}) on the modern_common_frontage "
             f"basis in 40_01_epoch_series.csv. Carries this pair's tag because "
             f"it is context FOR this pair, not a free-standing constant"),
        ]
        for name, val, unit, note_txt in pairs:
            rows.append({"Parameter": name, "Well": "", "Era": era,
                         "Value": val, "Unit": unit, "Note": note_txt})
    return pd.DataFrame(rows)


# ======================================================================
# The gate
# ======================================================================
def _evaluate_gate(floor, control_worst, sagitta_bound):
    """Decide whether a rate may be emitted. Returns (ok, [reasons]).

    Every failure is NAMED. A gate that fails without saying why teaches the
    next reader to route around it.
    """
    reasons = []

    # 1. Floor. A field with no progradation anywhere, whose least-eroding
    #    point sits at or above the highest independently surveyed rate on the
    #    same frontage, is not a measurement of a shoreline.
    if floor is None:
        reasons.append("floor test: the floor interval could not be measured")
    else:
        # The no-progradation condition was DROPPED 2026-08-29 (Martin's ruling,
        # D-087). It caught the old series, but so did the min-rate condition,
        # and it over-triggers on a long span: a coast retreating at ~2.3 m/yr
        # for two decades retreating everywhere is expected, not suspicious. The
        # sub-intervals do carry progradation, so the field is not sign-locked,
        # and n_progradation is still emitted for every interval - reported,
        # not gated.
        if floor["min_rate_m_yr"] > PUBLISHED_MAX:
            reasons.append(
                f"floor test: least-eroding normal {floor['min_rate_m_yr']:.3f} m/yr "
                f"exceeds the published most-active-point rate {PUBLISHED_MAX:.3f} m/yr")

    # 2. Control. Absent is not a pass: with no fixed feature there is no
    #    evidence about registration at all.
    if control_worst is None:
        reasons.append("control test: no usable independent repeat tracing")
    elif TOL_CONTROL is None:
        reasons.append("control test: SHORE_CONTROL_TOLERANCE_M is unset "
                       "(deliberately — set it from the observed spread)")
    elif control_worst > TOL_CONTROL:
        reasons.append(f"control test: repeat-tracing p95 {control_worst:.3f} m "
                       f"exceeds {TOL_CONTROL:.3f} m")

    # 3. Generalisation.
    if TOL_GENERAL is None:
        reasons.append("generalisation test: SHORE_GENERALISATION_TOLERANCE_M is unset "
                       "(deliberately — set it from the measured bound)")
    elif sagitta_bound > TOL_GENERAL:
        reasons.append(f"generalisation test: chord-sagitta bound {sagitta_bound:.3f} m "
                       f"exceeds {TOL_GENERAL:.3f} m")

    return (len(reasons) == 0), reasons


def _assert_thresholds_can_fail(floor):
    """A tolerance that would not flag the present data is decoration.

    Asserted here rather than left to whoever reads the number later.
    """
    if floor is None or TOL_CONTROL is None:
        return
    signal = abs(floor["median_m"])
    if TOL_CONTROL >= 0.25 * signal:
        warn(f"SHORE_CONTROL_TOLERANCE_M = {TOL_CONTROL:.3f} m is not small "
             f"against the {signal:.3f} m displacement being measured — a gate "
             f"that admits a quarter of its own signal is decoration")


def _regression_test(edge_1899, line_2006, inland_xy):
    """Reproduce D-060's published long-run rate, 0.65 m/yr.

    Measured UNRESTRICTED, on D-060's own basis: imposing this project's masking
    on a historical result and then calling the difference a failure compares two
    different quantities. That was established the hard way -- restricting to the
    modern common frontage returned 87.8 m against a published 75.2 m, a 16.8%
    "failure" that was entirely the mask.

    The pairing changed on 2026-08-29 when DCoast_2015.kml was deleted as
    unverifiable. It is now 1899 dune edge -> 2006, and the RATE is compared,
    the endpoint no longer matching D-060's.
    """
    m = _measure(edge_1899, line_2006, 107.0, inland_xy)
    if m is None:
        warn("D-060 anchor produced no measurable normals")
        return None
    dev = abs(m["rate_m_yr"] - D060_RATE_M_YR) / D060_RATE_M_YR * 100.0
    ok = dev <= D060_TOLERANCE_PCT
    (info if ok else warn)(
        f"D-060 anchor: {m['rate_m_yr']:.3f} m/yr (from {m['median_m']:.3f} m over "
        f"107 yr) against published {D060_RATE_M_YR} m/yr "
        f"({dev:.1f}% — {'within' if ok else 'OUTSIDE'} {D060_TOLERANCE_PCT:.0f}%)")
    return {"median_m": m["median_m"], "rate_m_yr": m["rate_m_yr"],
            "deviation_pct": dev, "passed": ok}


def _synthetic_test(line, inland_xy):
    """A line translated landward by a known distance must measure as that.

    Independent of every historical file, so it cannot be lost when an input is
    withdrawn. The translation is applied along the mean seaward normal, and the
    measurement must return SYNTHETIC_OFFSET_M.
    """
    S, _ = _resample(line, SPACING_M)
    _, n_mean = _cone_mask(_normals(S, inland_xy))
    # LANDWARD, i.e. -n: the shifted line stands in for a LATER, retreated
    # shoreline, so the original is the seaward "earlier" one. Translating
    # seaward instead returns a correctly-signed progradation and reads as a
    # failure -- which is how this test found its own sign error on first run.
    shifted = line - SYNTHETIC_OFFSET_M * n_mean
    m = _measure(line, shifted, 1.0, inland_xy)
    if m is None:
        warn("synthetic anchor produced no measurable normals")
        return None
    err = abs(m["median_m"] - SYNTHETIC_OFFSET_M)
    ok = err <= SYNTHETIC_TOLERANCE_M
    (info if ok else warn)(
        f"synthetic anchor: a {SYNTHETIC_OFFSET_M:.1f} m translation measures as "
        f"{m['median_m']:.3f} m (error {err:.3f} m — "
        f"{'within' if ok else 'OUTSIDE'} {SYNTHETIC_TOLERANCE_M:.1f} m)")
    return {"measured_m": m["median_m"], "error_m": err, "passed": ok}


def _figure(measured, out_path):
    """Alongshore signed displacement, with the zero line and the survey band."""
    fig, ax = plt.subplots(figsize=(9, 5), facecolor="white")
    for (a, b), m in measured.items():
        if m is None or a == "1899":
            continue
        ok = m["_ok"]
        ax.plot(m["_arc"][ok] / 1000.0, m["_ray"][ok], lw=1.4,
                label=f"{a}–{b}  (median {m['median_m']:.1f} m)")
    fl = measured.get(FLOOR_INTERVAL)
    if fl is not None:
        band = PUBLISHED_MAX * fl["years"]
        ax.axhspan(-band, band, color="0.85", zorder=0,
                   label=f"± published most-active rate × {fl['years']:.0f} yr")
    ax.axhline(0.0, color="black", lw=1.0)
    ax.set_xlabel("alongshore distance (km, south → north)")
    ax.set_ylabel("signed shore-normal displacement (m)\npositive = retreat")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Shoreline displacement along the frontage")
    fig.tight_layout()
    render_figure(fig, out_path)
    plt.close(fig)


def _common_normals(nrm, base, epoch_line, lat0, lon0):
    """40_02 on COMMON transects (1.10.0): from each 2026 normal origin of the
    floor interval, the signed ray to every earlier line of
    COMMON_NORMAL_EPOCHS (positive = that line lies seaward, i.e. the dune edge
    has retreated since), and the consecutive retreat a->b = ray_a - ray_b on
    those same transects. Returns the frame and the car-park report rows."""
    S, N = base["_S"], base["_N"]
    ok = np.asarray(base["_ok"], dtype=bool)
    en = _local_to_osgb(S, lat0, lon0)
    nrm["E_osgb"], nrm["N_osgb"] = en[:, 0], en[:, 1]
    nrm["in_floor_band"] = ok
    for ep in COMMON_NORMAL_EPOCHS:
        nrm[f"ray_2026_to_{ep}_m"] = [(_ray_signed(S[k], N[k], epoch_line[ep], MAX_RANGE_M)
                                      if ok[k] else np.nan) for k in range(len(S))]
    seq = COMMON_NORMAL_EPOCHS + ("2026",)
    for a, b in zip(seq[:-1], seq[1:]):
        rb = 0.0 if b == "2026" else nrm[f"ray_2026_to_{b}_m"]
        nrm[f"common_{a}_{b}_m"] = nrm[f"ray_2026_to_{a}_m"] - rb
    rows = []
    loc = pd.read_csv(paths.INT_LOCATIONS)
    loc["well"] = loc["Name"].astype(str).str.strip().str.lower()
    cp = loc[loc["well"] == CAR_PARK_WELL]
    if cp.empty:
        warn(f"{CAR_PARK_WELL} not in {paths.INT_LOCATIONS.name}: no car-park stretch")
        nrm["car_park_stretch"] = False
        return nrm, rows
    ce, cn = float(cp["E"].iloc[0]), float(cp["N"].iloc[0])
    d_cp = np.hypot(nrm["E_osgb"] - ce, nrm["N_osgb"] - cn)
    d_cp = d_cp.where(ok)
    k0 = int(d_cp.idxmin())
    near = (np.hypot(nrm["E_osgb"] - nrm.loc[k0, "E_osgb"], nrm["N_osgb"] - nrm.loc[k0, "N_osgb"])
            <= CAR_PARK_RADIUS_M) & ok
    nrm["car_park_stretch"] = near
    info(f"car-park stretch: {int(near.sum())} transects within {CAR_PARK_RADIUS_M:.0f} m of the "
         f"frontage point nearest {CAR_PARK_WELL.upper()} ({nrm.loc[k0, 'E_osgb']:.0f} E, "
         f"{nrm.loc[k0, 'N_osgb']:.0f} N; {d_cp.min():.0f} m from the well)")
    for a, b in zip(seq[:-1], seq[1:]):
        col = f"common_{a}_{b}_m"
        v_cp, v_all = nrm.loc[near, col].dropna(), nrm.loc[ok, col].dropna()
        info(f"    {a}->{b}: car park median {v_cp.median():+.1f} m (n {len(v_cp)}, "
             f"range {v_cp.min():+.1f} to {v_cp.max():+.1f}); whole band {v_all.median():+.1f} m "
             f"(n {len(v_all)})")
        for tag, v in (("carpark", v_cp), ("common_frontage", v_all)):
            rows.append({"Parameter": f"{tag}_retreat_{a}_{b}_median_m", "Well": "",
                         "Era": f"{a}-{b}", "Value": float(v.median()) if len(v) else np.nan,
                         "Unit": "m",
                         "Note": f"1.10.0: 40_02 column {col} (ray from the 2026 normals; positive = "
                                 f"retreat), median over {len(v)} transects"
                                 + (f" within {CAR_PARK_RADIUS_M:.0f} m of the frontage point nearest "
                                    f"{CAR_PARK_WELL.upper()} (the beach car park)" if tag == "carpark"
                                    else " of the floor band")})
    return nrm, rows


# ======================================================================
# Storm winters (1.10.0; Martin 2026-11-25: "a storm table")
# ======================================================================
# Onshore for this frontage: the wind from the south-west quadrant and either
# side of it, 180-300 deg true (Caernarfon Bay faces SW). Thresholds in knots,
# the unit MIDAS records (wind_speed_unit_id 4, confirmed from each file's
# header in utils.pet_alternatives.midas_hourly_wind): 34 kt is Beaufort 8
# (gale), 41 kt Beaufort 9 (severe gale). An EVENT is a day whose strongest
# onshore hourly mean reaches STORM_EVENT_KT. "Hourly mean" is the SYNOP
# 10-minute mean reported each hour; the gust is the 10-minute maximum gust,
# which SYNOP reports only when it is notable, so most hours carry none.
STORM_ONSHORE_DEG = (180.0, 300.0)
STORM_GALE_KT = 34.0
STORM_SEVERE_KT = 41.0
STORM_EVENT_KT = 40.0
STORM_WINTERS = ("2004-07-01", "2023-06-30 23:59")   # July-June winters 2004/05-2022/23
# Tides (Holyhead, BODC processed 15-minute files, placed by Martin in
# paths.DATA_TIDES_HOLYHEAD; see data/TIDES_PROVENANCE.md). A storm day
# "coincides with high water" when the day's highest observed level exceeds
# the winter's STORM_HW_PERCENTILE of daily highest levels.
STORM_HW_PERCENTILE = 95.0
BODC_BAD_FLAGS = ("M", "N", "T")   # improbable, null, interpolated
# Waves (1.11.0): a day is a high-wave day when its largest ERA5 hourly Hs at the
# frontage point exceeds the RECORD's STORM_HS_PERCENTILE of daily maxima (one
# threshold for every winter, so winters compare; the tide threshold is per
# winter because the nodal cycle moves high water between winters).
STORM_HS_PERCENTILE = 95.0
# The well-drop windows shaded on 40_11: the span of the 25_21 best-step dates
# of each first_step_group (Script 25 1.41.0), read from the committed file.
STORM_DROP_GROUPS = ("2009", "2014-15")


def _winter_label(t: pd.Timestamp) -> str:
    y = t.year if t.month >= 7 else t.year - 1
    return f"{y}/{str(y + 1)[2:]}"


def _read_bodc(folder):
    """BODC processed tide-gauge files (one per year, *.txt, stored gzipped as
    *.txt.gz since 1.11.0): 15-minute observed level and the residual (observed
    minus predicted) the files carry, in m. Values flagged M (improbable), N
    (null) or T (interpolated) are dropped: the M values include impossible ones
    (Holyhead 2010 to 32.19 m) in whole flagged months, so BODC's judgement is
    taken as it stands. Only the folder's top level is read (its recent/
    monthly files overlap the last yearly one). None when it holds no file."""
    fd = pathlib.Path(folder)
    files = sorted(list(fd.glob("*.txt")) + list(fd.glob("*.txt.gz"))) if fd.exists() else []
    if not files:
        return None
    pat = re.compile(r"^\s*\d+\)\s+(\d{4}/\d\d/\d\d)\s+(\d\d:\d\d:\d\d)\s+(-?\d+\.\d+)([A-Z]?)\s+(-?\d+\.\d+)([A-Z]?)")
    rows = []
    for f in files:
        raw = gzip.decompress(f.read_bytes()) if f.suffix == ".gz" else f.read_bytes()
        for line in raw.decode("utf-8", errors="replace").splitlines():
            m = pat.match(line)
            if m:
                rows.append((m.group(1) + " " + m.group(2),
                             np.nan if m.group(4) in BODC_BAD_FLAGS else float(m.group(3)),
                             np.nan if m.group(6) in BODC_BAD_FLAGS else float(m.group(5))))
    if not rows:
        warn(f"{folder}: {len(files)} file(s) but no BODC data line parsed — tide columns empty")
        return None
    tz = pd.DataFrame(rows, columns=["t", "level_m", "residual_m"])
    tz["t"] = pd.to_datetime(tz["t"], format="%Y/%m/%d %H:%M:%S")
    return tz.set_index("t").sort_index()


def _read_era5_waves(path):
    """ERA5 hourly waves at the frontage grid point (1.11.0): time_utc, swh_m (significant height of combined wind
    waves and swell), mwd_deg (mean direction, from), pp1d_s (peak period). The CSV is the conversion of the CDS
    NetCDF files by data/waves/era5_to_csv.py (the venv carries no NetCDF4 reader). None when absent."""
    if not pathlib.Path(path).exists():
        return None
    wv = pd.read_csv(path, parse_dates=["time_utc"])
    return wv.set_index("time_utc").sort_index()


def _storm_tables(drop_windows):
    """40_09 (per winter) and 40_10 (per event day) from MIDAS Valley hourly wind,
    with Holyhead tide columns when the BODC files are present."""
    from utils.pet_alternatives import midas_hourly_wind
    h = midas_hourly_wind(paths.MIDAS_WEATHER_DIR, *STORM_WINTERS)
    lo, hi = STORM_ONSHORE_DEG
    h["onshore"] = (h["wind_direction"] >= lo) & (h["wind_direction"] <= hi)
    h["on_speed"] = h["wind_speed"].where(h["onshore"])
    h["day"] = h.index.normalize()
    g = h.groupby("day")
    day = pd.DataFrame({"on_max_kt": g["on_speed"].max(), "gust_max_kt": g["q10mnt_mxgst_spd"].max(),
                        "msl_min_hpa": g["msl_pressure"].min(), "n_hours": g["wind_speed"].count()})
    idx = h.dropna(subset=["on_speed"]).groupby("day")["on_speed"].idxmax()
    day["dir_at_max_deg"] = h.loc[idx.values, "wind_direction"].set_axis(idx.index)
    day["winter"] = [_winter_label(t) for t in day.index]
    tide = _read_bodc(paths.DATA_TIDES_HOLYHEAD)
    if tide is None:
        warn(f"no BODC tide files in {paths.DATA_TIDES_HOLYHEAD} (see data/TIDES_PROVENANCE.md): "
             "40_09 / 40_10 tide columns written EMPTY")
        day["hw_max_m"] = day["surge_max_m"] = np.nan
    else:
        tg = tide.groupby(tide.index.normalize())
        day["hw_max_m"] = tg["level_m"].max().reindex(day.index)
        day["surge_max_m"] = tg["residual_m"].max().reindex(day.index)
        info(f"Holyhead tides: {len(tide)} readings {tide.index.min():%Y-%m-%d} to {tide.index.max():%Y-%m-%d}")
    # 1.11.0: Barmouth, the gauge south of the frontage, beside Holyhead to its north (own columns, never averaged).
    tide_b = _read_bodc(paths.DATA_TIDES_BARMOUTH)
    if tide_b is None:
        warn(f"no BODC tide files in {paths.DATA_TIDES_BARMOUTH}: Barmouth columns written EMPTY")
        day["hw_max_barmouth_m"] = day["surge_max_barmouth_m"] = np.nan
    else:
        tb = tide_b.groupby(tide_b.index.normalize())
        day["hw_max_barmouth_m"] = tb["level_m"].max().reindex(day.index)
        day["surge_max_barmouth_m"] = tb["residual_m"].max().reindex(day.index)
        info(f"Barmouth tides: {len(tide_b)} readings {tide_b.index.min():%Y-%m-%d} to "
             f"{tide_b.index.max():%Y-%m-%d}")
    # 1.11.0: ERA5 waves at the grid point off the frontage (data/WAVES_PROVENANCE.md).
    wv = _read_era5_waves(paths.DATA_WAVES_ERA5)
    if wv is None:
        warn(f"{paths.DATA_WAVES_ERA5.name} absent (see data/WAVES_PROVENANCE.md): wave columns written EMPTY")
        day["hs_max_m"] = day["tp_at_hs_max_s"] = day["mwd_at_hs_max_deg"] = np.nan
        hs_thr = np.nan
    else:
        wv = wv[(wv.index >= pd.Timestamp(STORM_WINTERS[0])) & (wv.index <= pd.Timestamp(STORM_WINTERS[1]))]
        wv_ok = wv.dropna(subset=["swh_m"])
        wv_ok = wv_ok.assign(day=wv_ok.index.normalize())
        imax = wv_ok.groupby("day")["swh_m"].idxmax()
        at = wv_ok.loc[imax.values].set_axis(imax.index)
        day["hs_max_m"] = at["swh_m"].reindex(day.index)
        day["tp_at_hs_max_s"] = at["pp1d_s"].reindex(day.index)
        day["mwd_at_hs_max_deg"] = at["mwd_deg"].reindex(day.index)
        hs_thr = float(np.nanpercentile(day["hs_max_m"], STORM_HS_PERCENTILE))
        info(f"ERA5 waves: {len(wv_ok)} hours {wv_ok.index.min():%Y-%m-%d} to {wv_ok.index.max():%Y-%m-%d}; "
             f"record {STORM_HS_PERCENTILE:g}th percentile of daily maximum Hs {hs_thr:.2f} m")
    day["gale"] = day["on_max_kt"] >= STORM_GALE_KT
    day["severe"] = day["on_max_kt"] >= STORM_SEVERE_KT
    wrows = []
    for w, d in day.groupby("winter", sort=True):
        thr = (float(np.nanpercentile(d["hw_max_m"], STORM_HW_PERCENTILE))
               if d["hw_max_m"].notna().any() else np.nan)
        i_on = d["on_max_kt"].idxmax() if d["on_max_kt"].notna().any() else None
        i_p = d["msl_min_hpa"].idxmin() if d["msl_min_hpa"].notna().any() else None
        wrows.append({
            "winter": w, "start": f"{d.index.min():%Y-%m-%d}", "end": f"{d.index.max():%Y-%m-%d}",
            "n_days_with_wind": int((d["n_hours"] > 0).sum()),
            "gale_days_onshore": int(d["gale"].sum()), "severe_gale_days_onshore": int(d["severe"].sum()),
            "event_days": int((d["on_max_kt"] >= STORM_EVENT_KT).sum()),
            "max_onshore_mean_kt": float(d["on_max_kt"].max()),
            "max_onshore_mean_date": f"{i_on:%Y-%m-%d}" if i_on is not None else "",
            "max_gust_kt": float(d["gust_max_kt"].max()),
            "min_msl_hpa": float(d["msl_min_hpa"].min()),
            "min_msl_date": f"{i_p:%Y-%m-%d}" if i_p is not None else "",
            "tide_days_holyhead": int(d["hw_max_m"].notna().sum()),
            "tide_days_barmouth": int(d["hw_max_barmouth_m"].notna().sum()),
            "hw_threshold_m": thr,
            "gale_days_above_hw_threshold": (int((d["gale"] & (d["hw_max_m"] > thr)).sum())
                                             if np.isfinite(thr) else np.nan),
            "max_surge_m": float(d["surge_max_m"].max()) if d["surge_max_m"].notna().any() else np.nan,
            "max_surge_barmouth_m": (float(d["surge_max_barmouth_m"].max())
                                     if d["surge_max_barmouth_m"].notna().any() else np.nan),
            "max_hs_m": float(d["hs_max_m"].max()) if d["hs_max_m"].notna().any() else np.nan,
            "max_hs_date": f"{d['hs_max_m'].idxmax():%Y-%m-%d}" if d["hs_max_m"].notna().any() else "",
            "hs_threshold_m": hs_thr,
            "days_hs_above_threshold": (int((d["hs_max_m"] > hs_thr).sum()) if np.isfinite(hs_thr) else np.nan),
            "gale_days_hs_above_threshold": (int((d["gale"] & (d["hs_max_m"] > hs_thr)).sum())
                                             if np.isfinite(hs_thr) else np.nan),
        })
    winters = pd.DataFrame(wrows)
    ev = day[day["on_max_kt"] >= STORM_EVENT_KT].copy()
    events = pd.DataFrame({
        "date": [f"{t:%Y-%m-%d}" for t in ev.index], "winter": ev["winter"].values,
        "max_onshore_mean_kt": ev["on_max_kt"].values, "dir_at_max_deg": ev["dir_at_max_deg"].values,
        "max_gust_kt": ev["gust_max_kt"].values, "min_msl_hpa": ev["msl_min_hpa"].values,
        "hw_max_m": ev["hw_max_m"].values, "surge_max_m": ev["surge_max_m"].values,
        "hw_max_barmouth_m": ev["hw_max_barmouth_m"].values, "surge_max_barmouth_m": ev["surge_max_barmouth_m"].values,
        "hs_max_m": ev["hs_max_m"].values, "tp_at_hs_max_s": ev["tp_at_hs_max_s"].values,
        "mwd_at_hs_max_deg": ev["mwd_at_hs_max_deg"].values,
        "in_drop_window": [next((lab for lab, (a, b) in drop_windows.items() if a <= t <= b), "")
                           for t in ev.index]})
    return winters, events


def _drop_windows():
    """The well-drop windows of 25_21 (first_step_group, min..max best-step
    date over the COASTAL wells preferring a drop), or {} when 25_21 is absent."""
    if not paths.OUT_25_STEP_VS_TREND.exists():
        warn(f"{paths.OUT_25_STEP_VS_TREND.name} absent: 40_11 draws no well-drop windows")
        return {}
    st = pd.read_csv(paths.OUT_25_STEP_VS_TREND)
    if "first_step_group" not in st.columns:
        warn(f"{paths.OUT_25_STEP_VS_TREND.name} has no first_step_group (Script 25 < 1.41.0): no windows")
        return {}
    out = {}
    for lab in STORM_DROP_GROUPS:
        s = st[(st["first_step_group"].astype(str) == lab) & st["prefers_drop"].astype(bool)
               & (st["group"] == "coastal")]
        if len(s):
            d = pd.to_datetime(s["step_date"] + "-01")
            out[lab] = (d.min(), d.max() + pd.offsets.MonthEnd(0))
    return out


def _storm_figure(winters, epoch_date, drop_windows, out_path):
    """40_11: onshore gale and severe-gale days per winter, the shoreline epochs
    and the well-drop windows."""
    fig, ax = plt.subplots(figsize=(10, 4.8), facecolor="white")
    x = np.array([int(w[:4]) + 1.0 for w in winters["winter"]])   # mid-winter, 1 January
    ax.bar(x - 0.2, winters["gale_days_onshore"], 0.4, color="#4c72b0",
           label=f"days with onshore mean ≥ {STORM_GALE_KT:.0f} kt (gale)")
    ax.bar(x + 0.2, winters["severe_gale_days_onshore"], 0.4, color="#c44e52",
           label=f"days with onshore mean ≥ {STORM_SEVERE_KT:.0f} kt (severe gale)")
    for (lab, (a, b)), col in zip(drop_windows.items(), ("#f0c040", "#90c890")):
        ax.axvspan(a.year + (a.dayofyear - 1) / 365.25, b.year + b.dayofyear / 365.25, color=col,
                   alpha=0.45, zorder=0, label=f"coastal well drops, {lab} group ({a:%b %Y}–{b:%b %Y})")
    ymax = max(1.0, float(winters["gale_days_onshore"].max()))
    for name, t in epoch_date.items():
        if name == "1899":
            continue
        xv = t.year + (t.dayofyear - 1) / 365.25
        ax.axvline(xv, color="0.3", ls="--", lw=0.9, zorder=1)
        ax.text(xv, ymax * 1.45, name, ha="center", va="bottom", fontsize=8.5, color="0.3",
                bbox=dict(fc="white", ec="none", pad=0.5))
    ax.set_xlim(2004.3, 2026.6)
    ax.set_ylim(0, ymax * 1.55)
    ax.set_xticks(range(2005, 2027, 2))
    ax.set_xlabel("winter (July–June), plotted at 1 January")
    ax.set_ylabel("days per winter")
    ax.set_title("Onshore (180–300°) gales at Valley, with the shoreline epochs (dashed)", fontsize=11)
    ax.legend(fontsize=8, frameon=False, loc="upper right", bbox_to_anchor=(1.0, 0.93), ncol=2)
    fig.tight_layout()
    render_figure(fig, out_path)
    plt.close(fig)


def _storm_report_rows(winters, events):
    rows = []

    def _r(k, v, u, era, note):
        rows.append({"Parameter": k, "Well": "", "Era": era, "Unit": u,
                     "Value": float(v) if pd.notna(v) else np.nan, "Note": note})
    span = f"{winters['winter'].iloc[0]}-{winters['winter'].iloc[-1]}"
    _r("storm_n_winters", len(winters), "winters", span, "40_09: July-June winters with MIDAS Valley hourly wind")
    _r("storm_gale_days_median", winters["gale_days_onshore"].median(), "days", span,
       f"40_09: median per winter of days with an onshore (180-300 deg) hourly mean >= {STORM_GALE_KT:g} kt")
    _r("storm_severe_gale_days_median", winters["severe_gale_days_onshore"].median(), "days", span,
       f"40_09: median per winter of days with an onshore hourly mean >= {STORM_SEVERE_KT:g} kt")
    _r("storm_n_events", len(events), "days", span,
       f"40_10: days with an onshore hourly mean >= {STORM_EVENT_KT:g} kt")
    _r("storm_max_onshore_mean_kt", winters["max_onshore_mean_kt"].max(), "kt", span,
       "40_09: strongest onshore hourly mean of the record")
    for r in winters.itertuples():
        tag = r.winter.replace("/", "_")
        _r(f"storm_gale_days_{tag}", r.gale_days_onshore, "days", r.winter, "40_09 gale_days_onshore")
        _r(f"storm_severe_gale_days_{tag}", r.severe_gale_days_onshore, "days", r.winter,
           "40_09 severe_gale_days_onshore")
    return rows


# Length of each transect as drawn on 40_08 (m landward / seaward of the 2006
# line). Display only: the measurement is the signed ray of 40_02.
MAP_TRANSECT_LANDWARD_M = 200.0
MAP_TRANSECT_SEAWARD_M = 100.0


def _local_to_osgb(xy, lat0, lon0):
    """Inverse of _to_local_m, then WGS84 -> OSGB36 (EPSG:27700)."""
    r = 6371000.0
    xy = np.atleast_2d(np.asarray(xy, dtype=float))
    lon = lon0 + np.degrees(xy[:, 0] / (r * math.cos(math.radians(lat0))))
    lat = lat0 + np.degrees(xy[:, 1] / r)
    e, n = Transformer.from_crs("EPSG:4326", "EPSG:27700",
                                always_xy=True).transform(lon, lat)
    return np.column_stack([e, n])


def _transect_map(epoch_line, base, lat0, lon0, out_path):
    """40_08: the modern coastlines, the shore-normal transects coloured by
    their 2006-2026 signed retreat, the clay exposure and Script 38's transect
    wells joined as a line, on the project's site layers and E/N axes."""
    from matplotlib.collections import LineCollection
    fig, ax = plt.subplots(figsize=(8.0, 7.2), facecolor="white")
    add_kml_features(ax, paths.DATA_DIR, include_scrapes=False)
    pts = []
    styles = {"2006": ("0.55", "--"), "2009": ("#2ca02c", ":"), "2017": ("#1f77b4", "-"),
              "2021": ("#9467bd", "-"), "2026": ("black", "-")}
    for name in ("2006", "2009", "2017", "2021", "2026"):
        xy = _local_to_osgb(epoch_line[name], lat0, lon0)
        pts.append(xy)
        col, ls = styles[name]
        ax.plot(xy[:, 0], xy[:, 1], color=col, ls=ls, lw=1.4, zorder=4,
                label=f"coastline {name}")
    S, N, ray = base["_S"], base["_N"], base["_ray"]
    ok = np.asarray(base["_ok"], dtype=bool) & np.isfinite(ray)
    a = _local_to_osgb(S[ok] - MAP_TRANSECT_LANDWARD_M * N[ok], lat0, lon0)
    b = _local_to_osgb(S[ok] + MAP_TRANSECT_SEAWARD_M * N[ok], lat0, lon0)
    segs = np.stack([a, b], axis=1)
    lim = float(np.nanpercentile(np.abs(ray[ok]), 98))
    lc = LineCollection(segs, array=ray[ok], cmap="RdBu_r", norm=plt.Normalize(-lim, lim),
                        linewidths=1.3, zorder=3)
    ax.add_collection(lc)
    cb = fig.colorbar(lc, ax=ax, shrink=0.6, pad=0.02)
    cb.set_label("signed retreat 2006–2026 (m)\npositive = landward", fontsize=10)
    cb.ax.tick_params(labelsize=9.5)
    pts.append(segs.reshape(-1, 2))
    if paths.DATA_KML_CLAY.exists():
        tr = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
        for ll in _read_kml(paths.DATA_KML_CLAY):
            e, n = tr.transform(ll[:, 0], ll[:, 1])
            ax.plot(e, n, color="saddlebrown", lw=2.6, zorder=5, solid_capstyle="round",
                    label="clay exposure (clay.kml)")
            pts.append(np.column_stack([e, n]))
    else:
        warn(f"{paths.DATA_KML_CLAY.name} not found: the clay exposure is not drawn")
    if paths.OUT_38_CSV.exists():
        wells = [c for c in pd.read_csv(paths.OUT_38_CSV, nrows=0).columns
                 if c not in ("year",) and not c.startswith("diff")]
        loc = pd.read_csv(paths.INT_LOCATIONS)
        loc["well"] = loc["Name"].astype(str).str.strip().str.lower()
        dist = pd.read_csv(paths.DATA_DIST_COAST)
        dist["well"] = dist["Name"].astype(str).str.strip().str.lower()
        w = (loc[loc["well"].isin(wells)][["well", "E", "N"]]
             .merge(dist[["well", "dist_coast_m"]], on="well")
             .sort_values("dist_coast_m"))
        ax.plot(w["E"], w["N"], "-", color="darkorange", lw=1.8, zorder=6)
        ax.scatter(w["E"], w["N"], s=55, color="darkorange", edgecolor="black", zorder=7,
                   label="Script 38 transect wells")
        for r in w.itertuples():
            ax.annotate(r.well.upper(), (r.E, r.N), xytext=(5, 4), textcoords="offset points",
                        fontsize=9, zorder=8)
        pts.append(w[["E", "N"]].to_numpy(dtype=float))
    else:
        warn(f"{paths.OUT_38_CSV.name} not found: the Script 38 transect wells are not drawn")
    allp = np.vstack(pts)
    pad = 250.0
    ax.set_xlim(allp[:, 0].min() - pad, allp[:, 0].max() + pad)
    ax.set_ylim(allp[:, 1].min() - pad, allp[:, 1].max() + pad)
    add_en_axes(ax, apply_extent=False, labelsize=9.5, label_fontsize=10.5)
    ax.legend(fontsize=9, loc="lower left", frameon=True, framealpha=0.9)
    ax.set_title("Shore-normal transects, 2006–2026 retreat", fontsize=12)
    fig.tight_layout()
    render_figure(fig, out_path)
    plt.close(fig)


# ======================================================================
def main():
    banner(SCRIPT_ID, "Shoreline retreat from the digitised coastline epochs",
           VERSION)
    # The script creates its own output directory, as Scripts 30, 32, 34, 35, 36,
    # 37, 37b, 38 and 39 do. paths.py used to do it at import, which meant every
    # module in the project created this directory just by importing paths.
    paths.DIR_40.mkdir(parents=True, exist_ok=True)

    phase(1, "Loading coastline epochs")
    raw = {name: _read_kml(path) for name, path, _ in EPOCHS}
    lat0, lon0 = _projection_origin([a for name, v in raw.items()
                                     if name in ORIGIN_EPOCHS for a in v])
    info(f"local projection origin {lat0:.4f} N, {lon0:.4f} E")

    global _ORIGIN
    _ORIGIN = (lat0, lon0)
    lines = {name: [_to_local_m(a, lat0, lon0) for a in v] for name, v in raw.items()}
    site = load_site_outline()
    if site is None:
        raise SystemExit("40: the site outline is required for the inland reference")
    c_lon, c_lat = Transformer.from_crs("EPSG:27700", "EPSG:4326",
                                        always_xy=True).transform(site.centroid.x, site.centroid.y)
    inland_xy = _to_local_m(np.array([[c_lon, c_lat]]), lat0, lon0)[0]
    info(f"inland reference (site-outline centroid) at "
         f"{inland_xy[0]:.0f}, {inland_xy[1]:.0f} m local")

    edge_i, hwm_i, meds = _identify_1899_lines(lines["1899"], lines["2026"][0], inland_xy)
    info(f"coast1899 placemarks resolved by measurement, not index order: "
         f"dune edge = placemark {edge_i} (median {meds[edge_i]:.1f} m to 2020), "
         f"high water = placemark {hwm_i} ({meds[hwm_i]:.1f} m)")
    epoch_line = {"1899": lines["1899"][edge_i], "2006": lines["2006"][0],
                  "2009": lines["2009"][0], "2017": lines["2017"][0], "2021": lines["2021"][0],
                  "2026": lines["2026"][0]}
    epoch_date = {n: pd.Timestamp(d) for n, _, d in EPOCHS}

    phase(2, "Common frontage and normal orientation")
    keep_lo, keep_hi = _common_extent(
        [epoch_line[n] for n in MODERN_BAND_EPOCHS], SPACING_M)
    _lo9, _hi9 = _common_extent([epoch_line[n] for n in MODERN_BAND_EPOCHS + ("2009",)], SPACING_M)
    if (_lo9, _hi9) != (keep_lo, keep_hi):
        warn(f"coast2009 does NOT span the modern band ({_lo9:.0f}-{_hi9:.0f} against "
             f"{keep_lo:.0f}-{keep_hi:.0f} m): its intervals on that band are partial")
    info(f"common northing band {keep_lo:.0f} to {keep_hi:.0f} m local "
         f"(span {keep_hi - keep_lo:.0f} m) — restricted by EXTENT, not hit-success")
    S_chk, _ = _resample(epoch_line["2026"], SPACING_M)
    N_chk = _normals(S_chk, inland_xy)
    good, _mean = _cone_mask(N_chk)
    brg = _bearings_deg(N_chk)
    bad = int((~good).sum())
    frac = bad / len(good)
    if frac > 0.05:
        raise RuntimeError(f"{bad} of {len(good)} seaward normals ({frac:.0%}) fall "
                           f"outside the cone — orientation is unreliable on this "
                           f"frontage; refusing to measure")
    info(f"seaward normals {np.percentile(brg[good], 1):.0f}–"
         f"{np.percentile(brg[good], 99):.0f} deg across {int(good.sum())} normals; "
         f"{bad} degenerate ({frac:.1%}) excluded")

    phase(3, "Signed shore-normal displacement")
    # Primary basis: each interval on the common extent of ITS OWN two lines,
    # which is what the spec says ("all lines in the comparison"). The modern
    # three are ALSO measured on the shared modern band, because the
    # acceleration claim compares them with each other and needs a like-for-like
    # basis. Both are emitted, labelled, rather than one being chosen silently:
    # the extent choice is nearly free on the modern series and moves the 1899
    # comparison by 16%, so which basis is in use is not a detail.
    measured, modern_common = {}, {}
    years = {}
    for a, b in INTERVALS:
        yrs = (epoch_date[b] - epoch_date[a]).days / DAYS_PER_YEAR
        years[(a, b)] = yrs
        lo, hi = _common_extent([epoch_line[a], epoch_line[b]], SPACING_M)
        m = _measure(epoch_line[a], epoch_line[b], yrs, inland_xy, lo, hi)
        measured[(a, b)] = m
        if m is None:
            warn(f"{a}→{b}: no measurable normals")
            continue
        step(f"{a}→{b}: median {m['median_m']:.3f} m over {yrs:.1f} yr "
             f"= {m['rate_m_yr']:.3f} m/yr  (n={m['n']}, "
             f"progradation {m['n_progradation']}, nearest {m['nearest_median_m']:.3f} m)")
    for a, b in MODERN_INTERVALS:
        mc = _measure(epoch_line[a], epoch_line[b], years[(a, b)], inland_xy,
                      keep_lo, keep_hi)
        modern_common[(a, b)] = mc
        if mc is not None:
            info(f"    on the shared modern frontage: {a}→{b} "
                 f"{mc['median_m']:.3f} m = {mc['rate_m_yr']:.3f} m/yr (n={mc['n']})")

    phase(4, "Diagnostics")
    gen_df, sagitta = _generalisation_bound(
        [epoch_line[n] for n in ("2006", "2017", "2021", "2026")],
        ["coast2006", "coast2017", "coast2021", "coast2026"])
    info(f"chord-sagitta bound {sagitta:.3f} m (measured, not densified away)")
    ctl_df, ctl_worst = _control(epoch_line["2006"], inland_xy)
    if ctl_worst is None:
        note("repeat-tracing control: unavailable or rejected — see 40_03_control.csv")
    else:
        info(f"repeat-tracing control: |offset| median "
             f"{ctl_df.iloc[0]['median_abs_m']:.3f} m, p95 {ctl_worst:.3f} m "
             f"across {int(ctl_df.iloc[0]['n'])} normals, 0 shared vertices")
    dtm_df = (_dtm_profile(modern_common[FLOOR_INTERVAL], lat0, lon0)
              if modern_common.get(FLOOR_INTERVAL) else pd.DataFrame())
    sens_df = _coastal_sensitivity(modern_common, epoch_date)

    phase(5, "Storm pair — displacement, not rate")
    ctx = modern_common.get(STORM_CONTEXT_INTERVAL)
    if ctx is None:
        warn(f"storm-pair context interval {STORM_CONTEXT_INTERVAL} was not "
             f"measured — the between-storm expectation will be NA")
        context = (float("nan"), "unavailable", float("nan"))
    else:
        context = (ctx["rate_m_yr"],
                   f"{STORM_CONTEXT_INTERVAL[0]}-{STORM_CONTEXT_INTERVAL[1]}",
                   ctx["years"])
    storm_df = _storm_pair(inland_xy, ctl_worst, context)
    rn_df = _report_numbers(storm_df, context) if len(storm_df) else pd.DataFrame()

    phase(6, "Anchors")
    reg = _regression_test(epoch_line["1899"], epoch_line["2006"], inland_xy)
    syn = _synthetic_test(epoch_line["2026"], inland_xy)

    phase(7, "Gate")
    floor = modern_common.get(FLOOR_INTERVAL)
    _assert_thresholds_can_fail(floor)
    ok, reasons = _evaluate_gate(floor, ctl_worst, sagitta)
    if ok:
        result("headline", "EMITTED — all three gate tests pass")
    else:
        warn("HEADLINE WITHHELD — rate_m_yr written as NA. Reasons:")
        for r in reasons:
            warn(f"    {r}")
    withheld_reason = "" if ok else "; ".join(reasons)

    # T-91: the modern_common_frontage 2006-2026 rate as a free-standing report
    # number. This is the same value the epoch series carries at
    # (from_epoch=2006, to_epoch=2026, basis=modern_common_frontage); it is
    # repeated here, read from the same in-memory `modern_common` dict and the
    # same gate result, so it can be cited without a reader having to filter
    # 40_01_epoch_series.csv by basis and epoch pair.
    headline = modern_common.get(("2006", "2026"))
    if headline is not None:
        rn_df = pd.concat([rn_df, pd.DataFrame([{
            "Parameter": "headline_retreat_rate_2006_2026_m_yr",
            "Well": "", "Era": "2006-2026",
            "Value": headline["rate_m_yr"] if ok else float("nan"),
            "Unit": "m/yr",
            "Note": "modern_common_frontage basis (40_01_epoch_series.csv); "
                    "emitted because the floor, control and generalisation "
                    "gate tests pass; NaN if withheld",
        }])], ignore_index=True)

    # T-96 batch 2: the 1899 georeferencing RMSE as a rate over the 1899->2006
    # pair_extent span (the `years` that row of 40_01 carries).
    _m1899 = measured.get(("1899", "2006"))
    if _m1899 is not None:
        rn_df = pd.concat([rn_df, pd.DataFrame([{
            "Parameter": "shoreline_1899_georef_rmse_rate_m_per_yr",
            "Well": "", "Era": "1899-2006",
            "Value": config.SHORELINE_1899_GEOREF_RMSE_M / _m1899["years"],
            "Unit": "m/yr",
            "Note": f"SHORELINE_1899_GEOREF_RMSE_M ({config.SHORELINE_1899_GEOREF_RMSE_M:g} m, "
                    f"data/geo/GEO_PROVENANCE.md) / years of the 1899->2006 pair_extent row "
                    f"of 40_01_epoch_series.csv ({_m1899['years']:.3f} yr)",
        }])], ignore_index=True)

    phase(8, "Writing outputs")
    rows = []

    def _row(a, b, m, basis, gated=True):
        row = {"from_epoch": a, "to_epoch": b, "basis": basis,
               "from_date": epoch_date[a].date().isoformat() if a in epoch_date else a,
               "to_date": epoch_date[b].date().isoformat() if b in epoch_date else b}
        row.update({k: v for k, v in m.items() if not k.startswith("_")})
        emit = ok or not gated
        row["rate_m_yr"] = m["rate_m_yr"] if emit else np.nan
        row["min_rate_m_yr"] = m["min_rate_m_yr"] if emit else np.nan
        row["withheld"] = (not emit)
        row["withheld_reason"] = "" if emit else withheld_reason
        row["estimator"] = "signed_shore_normal_ray"
        return row

    for (a, b), m in measured.items():
        if m is not None:
            rows.append(_row(a, b, m, "pair_extent"))
    for (a, b), m in modern_common.items():
        if m is not None:
            rows.append(_row(a, b, m, "modern_common_frontage"))
    if reg is not None:
        # The regression result belongs in a committed file, not only the
        # console: it is the evidence that the estimator still reproduces the
        # one published number this method can be checked against.
        rows.append({"from_epoch": "1899", "to_epoch": "2006",
                     "basis": "d060_anchor_unrestricted",
                     "from_date": "1899-01-01", "to_date": "2006-01-01",
                     # 107.0, not 116.0. The 116 was the 1899 -> 2015 DEM span
                     # of D-060 as first computed; when DCoast_2015.kml was
                     # deleted (D-087) and the anchor re-pointed to 1899 -> 2006,
                     # _regression_test moved to 107.0 and the docstring and
                     # console line moved with it, but this literal did not. The
                     # committed row therefore carried median 69.021 with years
                     # 116.0 and rate 0.645058 = 69.021/107, so recomputing the
                     # rate from the row's own two columns gave 0.595 -- 7.7% out.
                     "years": 107.0, "median_m": reg["median_m"],
                     "rate_m_yr": reg["rate_m_yr"],
                     "d060_published_rate_m_yr": D060_RATE_M_YR,
                     "deviation_pct": reg["deviation_pct"],
                     "withheld": False,
                     "withheld_reason": "" if reg["passed"] else "regression test FAILED",
                     "estimator": "signed_shore_normal_ray"})
    if syn is not None:
        rows.append({"from_epoch": "synthetic", "to_epoch": "synthetic",
                     "basis": "synthetic_translation_anchor",
                     "years": 1.0, "median_m": syn["measured_m"],
                     "rate_m_yr": syn["measured_m"],
                     "synthetic_offset_m": SYNTHETIC_OFFSET_M,
                     "error_m": syn["error_m"], "withheld": False,
                     "withheld_reason": "" if syn["passed"] else "synthetic anchor FAILED",
                     "estimator": "signed_shore_normal_ray"})
    series = pd.DataFrame(rows)
    series.to_csv(paths.OUT_40_EPOCH_SERIES, index=False)
    saved(paths.OUT_40_EPOCH_SERIES.name, f"{len(series)} intervals")

    base = modern_common[FLOOR_INTERVAL]
    nrm = pd.DataFrame({
        "index": np.arange(len(base["_S"])),
        "alongshore_m": base["_arc"],
        "E_local_m": base["_S"][:, 0], "N_local_m": base["_S"][:, 1],
        "normal_bearing_deg": _bearings_deg(base["_N"]),
    })
    for (a, b), m in modern_common.items():
        if m is not None and len(m["_ray"]) == len(nrm):
            nrm[f"signed_{a}_{b}_m"] = m["_ray"]
            nrm[f"nearest_{a}_{b}_m"] = m["_near"]
    nrm, cp_rows = _common_normals(nrm, base, epoch_line, lat0, lon0)
    rn_df = pd.concat([rn_df, pd.DataFrame(cp_rows)], ignore_index=True)
    nrm.to_csv(paths.OUT_40_NORMALS, index=False)
    saved(paths.OUT_40_NORMALS.name, f"{len(nrm)} normals")

    _write_or_preserve(ctl_df, paths.OUT_40_CONTROL,
                       "control absent" if ctl_worst is None else "{n} pairs")
    gen_df.to_csv(paths.OUT_40_GENERALISATION, index=False)
    saved(paths.OUT_40_GENERALISATION.name, f"bound {sagitta:.3f} m")
    _write_or_preserve(dtm_df, paths.OUT_40_DTM_PROFILE, "{n} rows")
    _write_or_preserve(sens_df, paths.OUT_40_SENSITIVITY, "{n} bases")
    # The storm pair goes to its OWN file, not into the epoch series. A row in
    # 40_01 would sit in a table whose every other row carries a rate, which is
    # how a displacement acquires one.
    storm_df.to_csv(paths.OUT_40_STORM_PAIR, index=False)
    saved(paths.OUT_40_STORM_PAIR.name, f"{len(storm_df)} pair(s), no rate emitted")
    for a, b in (("2006", "2009"), ("2009", "2017")):
        mc = modern_common.get((a, b))
        if mc is not None:
            rn_df = pd.concat([rn_df, pd.DataFrame([{
                "Parameter": f"retreat_{a}_{b}_median_m", "Well": "",
                "Era": f"{epoch_date[a].date()} to {epoch_date[b].date()}",
                "Value": mc["median_m"], "Unit": "m",
                "Note": f"1.10.0: signed shore-normal median on the modern_common_frontage "
                        f"band ({mc['n']} normals, {mc['years']:.2f} yr; rate in 40_01)"}])],
                ignore_index=True)
    rn_df.to_csv(paths.OUT_40_REPORT_NUMBERS, index=False)
    saved(paths.OUT_40_REPORT_NUMBERS.name, f"{len(rn_df)} value(s)")

    _figure(modern_common, paths.OUT_40_FIG)
    saved(paths.OUT_40_FIG.name)
    _transect_map(epoch_line, base, lat0, lon0, paths.OUT_40_TRANSECT_MAP)
    saved(paths.OUT_40_TRANSECT_MAP.name)

    phase(9, "Storm winters (MIDAS Valley wind; Holyhead tides when present)")
    drop_windows = _drop_windows()
    winters, events = _storm_tables(drop_windows)
    winters.to_csv(paths.OUT_40_STORM_WINTERS, index=False)
    saved(paths.OUT_40_STORM_WINTERS.name, f"{len(winters)} winters")
    events.to_csv(paths.OUT_40_STORM_EVENTS, index=False)
    saved(paths.OUT_40_STORM_EVENTS.name, f"{len(events)} event days")
    print(winters[["winter", "gale_days_onshore", "severe_gale_days_onshore", "event_days",
                   "max_onshore_mean_kt", "max_onshore_mean_date", "max_gust_kt", "min_msl_hpa"]]
          .to_string(index=False))
    _storm_figure(winters, epoch_date, drop_windows, paths.OUT_40_STORM_FIG)
    saved(paths.OUT_40_STORM_FIG.name)
    rn_df = pd.concat([rn_df, pd.DataFrame(_storm_report_rows(winters, events))], ignore_index=True)
    rn_df.to_csv(paths.OUT_40_REPORT_NUMBERS, index=False)
    saved(paths.OUT_40_REPORT_NUMBERS.name, f"{len(rn_df)} value(s), storm_* included")

    for a in (reg, syn):
        if a is not None and not a["passed"]:
            warn("an anchor failed — investigate before trusting anything above")
    done(SCRIPT_ID)


if __name__ == "__main__":
    main()
