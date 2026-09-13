#!/usr/bin/env python3
"""ingest_capture.py — read a new Google Earth screen capture and PROPOSE its row.

WHAT IT DOES, AND WHAT IT REFUSES TO DO

  It reads a capture and works out, from the pixels alone, when it was taken,
  where it sits on the ground, how well it registers, and whether it duplicates
  anything already in the series. It then prints a proposed filename and a
  proposed `aerial_manifest.csv` row.

  **It writes nothing into `data/geo/`.** Every field it produces is a proposal
  for Martin to confirm, for one reason: on 2026-09-12 two frames dated ten
  months apart turned out to carry the same imagery over the warren, and one of
  them had already been used to calibrate the gate before anyone noticed. A tool
  that files its own guesses would have filed that one too. The proposals land in
  `working/updates/` and the manifest is edited by hand.

  **The attribution line is never proposed.** It is a rights statement and the
  manifest's own standard is that it is READ FROM THE RENDERED IMAGE. That stays
  a human reading it.

HOW EACH FIELD IS OBTAINED

  date        OCR of the status bar (tesseract). Measured on the 157
              captures of 2026-09-12: 142 read from the bar, 0 inferred, 15
              undetermined. Of those 15, thirteen were inspected and the bar
              carries NO "Imagery Date" field at all — Google Earth did not
              render one — so no amount of OCR will produce one and they must be
              read from the timeline by hand. **A failure is reported as a
              failure, never guessed** — a silently wrong date is the expensive
              error here, not a missing one, and the inference that used to fill
              these frames was wrong four times in five.

              THE OCR IS A HARD DEPENDENCY ON A BINARY, not just on a pip
              package. `--check-ocr` proves the whole chain for the interpreter
              you are about to run, in one command, and is the first thing to
              try when every frame comes back undated.
  THE FIT HERE IS FOR IDENTIFICATION, NOT FOR PRODUCTION. Measured against the
  committed registration on `site24-3-2021m.png`: this tool returns 2.814 m/px
  and a 9.29 m median residual where `41_03_registration.csv` has 2.884 m/px and
  3.93 m. It is a single pass from one seed; Script 41 tries several seeds per
  constellation group and keeps the best, and chains groups together. **That
  remains the production registration.** Nine metres is ample to say which
  ground a frame covers and at roughly what scale, which is all this tool needs
  in order to name it and check it for duplicates.

  position    NOT from OCR. The blue control pins of `data/geo/georef_grid.kml`
              are detected in the frame and matched to their known OSGB
              coordinates, and the fitted homography gives the footprint, the
              ground sampling distance and the residual. The image locates
              itself, to the accuracy of the fit, with nothing typed.
  duplicates  Every existing vp2 measurement frame is compared with the new one
              over the warren, and the share of IDENTICAL pixels reported. A
              Google Earth timeline entry is a COMPOSITE, not a capture: a
              distinct date does not imply distinct ground. 100 % means one
              measurement wearing two dates; a partial share means a stale block
              grafted in from another date, as 2020-03-31 carries 10.6 % of
              September 2019.

Usage:
    python3 tools/ingest_capture.py <file-or-directory> [...]
    python3 tools/ingest_capture.py new/ --rot-step 2
"""
from __future__ import annotations

__version__ = "1.6.0"  # Hollingham (2026) - 2026-09-12. A hand-read date
#   register, `data/geo/capture_dates_by_hand.csv`, which OVERRIDES the
#   status bar and joins the candidate set. The bar is the timeline label,
#   not always the imagery: two captures read 5/27/2010 and 3/24/2017 and
#   are the same ground as twins whose bars read 12/31/2009 and 12/31/2016.
#   That is also how a date outside the enumerated sixteen gets in.
# 1.5.0  Hollingham (2026) - 2026-09-12. The twin fill
#   is a pass in the tool rather than a measurement beside it: a frame with
#   no fit of its own inherits the transform of a capture seconds away
#   whose ground is MEASURED identical over the analysed window, which on
#   this series is 67 of 83 frames at 0.51-2.0 % difference in ~46 icon
#   blobs. A different view differs on 33-89 % and is refused by name.
#   `spread_ratio` now reaches the report instead of printing nan.
# 1.4.0  Hollingham (2026) - 2026-09-12. The ring
#   brightness threshold is SWEPT rather than fixed, and the grid fit
#   chooses. A fixed min-channel > 200 registered 74 of 157 captures and
#   the 83 failures were darker frames whose white icons never reached it,
#   not frames without control: their ring counts rose from 9 to 25-99 when
#   the threshold dropped. Martin's third objection, and correct again.
# 1.3.0  Hollingham (2026) - 2026-09-12. Two changes to
#   the date, both measured on all 157 captures. The crop cascade gains
#   inverted-autocontrast and Otsu crops, which read the bars rendered over
#   bright sand that no fixed threshold can: 137 frames read to 142. And
#   the pair fill now does what its docstring always claimed - BOTH
#   neighbours must agree - because the nearer-neighbour rule it actually
#   used was wrong on four of the five fills the pixels could check. An
#   undetermined frame now names its candidate dates instead of picking
#   one. An early exit on two exact matches pays for the wider cascade.
# 1.1.0  Hollingham (2026) - 2026-09-12. The OCR
#   preflight now proves the tesseract BINARY and not just the pytesseract
#   binding: a missing binary raised once per crop, was swallowed, and
#   reported itself as "OCR saw ''" on every frame. The real reason is
#   named once, --check-ocr tests it alone, a mid-run tesseract failure is
#   surfaced once, and `ocr_raw` and `date_source` now reach the CSV on the
#   rows that need them.
# 1.0.0  Hollingham (2026) - 2026-09-12. New, for the
#   high-resolution capture (D-159). Proposes; never files.

import argparse
import importlib.util
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import numpy as np                                           # noqa: E402
import pandas as pd                                          # noqa: E402
from PIL import Image, ImageOps                              # noqa: E402

from utils.console_utils import banner, info, saved, step, warn  # noqa: E402
from utils.paths import DATA_GEO_DIR                          # noqa: E402
from utils.warren_mask import warren_on                       # noqa: E402

OUT = REPO / "working" / "updates"
GRID_CSV = DATA_GEO_DIR / "georef_grid.csv"
MANIFEST = DATA_GEO_DIR / "aerial_manifest.csv"
# DATES READ BY HAND, WHICH OVERRIDE THE BAR. Normally the bar is the evidence
# and this tool never overrules it. Two captures in the 2026-09-12 series showed
# that the bar is the TIMELINE LABEL and not always the imagery: `…17-05-08.png`
# reads 5/27/2010 and `…17-05-56.png` reads 3/24/2017, and Martin checked both in
# Google Earth — the imagery is 12/31/2009 and 12/31/2016. Each is the same
# ground as its twin (0.44 % and 0.47 % difference, 41 and 43 icon blobs), whose
# bar reads the December date. So a hand reading wins, and says so in the note
# column; it is also the only place a date outside the manifest can enter.
HAND_DATES = DATA_GEO_DIR / "capture_dates_by_hand.csv"
# The eye altitude and GSD of the committed vp2 fit, used ONLY to seed the
# rotation search. The fit itself comes from the control points.
REF_ALT_KM, REF_GSD_M = 3.70, 2.884285
IDENTICAL_TOL = 2          # grey levels; below this two pixels are the same
DUP_REPORT_FRAC = 0.005    # report any pair sharing more than this
# A fit whose residual exceeds this many PIXELS is not a registration, it is a
# coincidence. Added after the first run: matched against the wrong control set
# the tool returned 54 of 97 points at a 67.75 m residual and 4.39 m/px on a
# frame whose committed fit is 3.93 m and 2.884 m/px — and REPORTED IT AS
# REGISTERED. A tool that asserts success on nonsense is worse than one that
# fails, so this refuses instead.
MAX_RESIDUAL_PX = 5.0
# ...AND THE FIT MUST BE AT A POSSIBLE SCALE. A residual gate in PIXELS is not
# enough: on 2026-09-12 four captures matched the wrong control net at 1.65-2.05
# px, which looked fine, while the fitted GSD came out at 13.9-47.8 m/px and the
# residual in METRES was 24-79 m. A frame captured from 1.5 km cannot be 47 m
# per pixel. So the scale is bounded too, and the two nets are compared on the
# residual in METRES rather than in pixels - the residual that matters is on the
# ground, not on the screen.
MIN_GSD_M, MAX_GSD_M = 0.15, 8.0
# ...AND THE MATCHED POINTS MUST SPAN TWO DIMENSIONS. A homography fitted to
# COLLINEAR points is degenerate: it reproduces those points beautifully and
# says nothing about anything else. On 2026-09-12 all 42 "registrations" in a
# 157-capture set were exactly this. The control grid had been loaded from the
# CSV rather than the KML, so Google Earth drew plain rings instead of the blue
# pushpins `_detect_markers` keys on; the only blue left in frame was the UI,
# and the 11 "markers" found on every frame sat at rows 88-102 - one horizontal
# line, the time-slider widget. Matched against one ROW of a regular grid that
# returns a 1.7 px residual and a plausible 0.93 m/px, and every earlier gate
# passed it.
#
# The test is the aspect ratio of the matched points' own spread: the smaller
# principal axis must be at least this fraction of the larger.
MIN_SPREAD_RATIO = 0.15
# When the north-up seed already matches this many points this closely, the
# rotation search cannot improve on it and is skipped.
ROT_SKIP_POINTS, ROT_SKIP_PX = 20, 3.0
# The ring icon, measured off the 2026-09-12 captures: a bright near-neutral
# annulus about 10-12 px across with a hollow centre.
# THE BRIGHTNESS THRESHOLD IS SWEPT, NOT FIXED. v1.3.0 used min-channel > 200
# and registered 74 of 157 frames. The 83 failures were not short of rings on
# the ground, they were short of rings that cleared 200: the split was bimodal
# and clean — 48-101 rings detected on the frames that registered against a
# median of 12 on those that did not — and the failures are simply DARKER
# captures (frame median brightness 87-118), where a white icon over dark pine
# never reaches 200 in its dimmest channel. Dropping the threshold on four of
# the worst took their counts from 9 to 25, 39, 99 and 65.
#
# So every threshold is tried and THE GRID FIT PICKS THE WINNER, which is the
# only honest arbiter available: a sand patch admitted by a looser threshold
# cannot match a 250 m lattice, so a looser threshold can only win by finding
# more real control. The sweep starts at 200 so a frame that already registered
# is answered on the first pass and costs what it always did.
RING_BRIGHT_SWEEP = (200, 170, 145, 120, 100)
RING_NEUTRAL = 45
# A fit this good cannot be improved on by loosening further; stop sweeping.
RING_SWEEP_ENOUGH_POINTS, RING_SWEEP_ENOUGH_PX = 30, 3.0
RING_MIN_PX, RING_MAX_PX = 10, 120
RING_MIN_D, RING_MAX_D = 6, 20
RING_SQUARENESS, RING_MAX_FILL = 3, 0.72
# Captures come off the camera in PAIRS — a markers-ON and a markers-OFF of the
# same view, seconds apart — so a frame whose bar will not read sits beside one
# that did. The gap is measured from the SCREENSHOT FILENAME timestamp, not from
# the file mtime, which a copy would rewrite.
#
# TWO CAPTURES THIS CLOSE ARE NOT NECESSARILY THE SAME DATE, which is what
# v1.0.0 assumed. The tiles are walked date by date, so the seam between two
# dates is also seconds wide — and the frames whose bar fails cluster on exactly
# that seam. This window is therefore a necessary condition for the fill, never
# a sufficient one; agreement between both neighbours is what licenses it.
PAIR_SECONDS = 45.0
# ── inheriting a transform from the markers-ON twin ────────────────────────
# HALF THIS SERIES CANNOT SELF-LOCATE AND DOES NOT NEED TO. The captures come in
# blocks of four: two with the control net ON, two with it OFF, 5-12 s apart. In
# timestamp order the registered/not sequence reads `R R . . R R . .` almost
# without exception. The markers-OFF frames are the measurement frames — clean
# ground, no icons over it — and their transform is their twin's.
#
# THE CLAIM "SAME VIEW" IS MEASURED, NOT INFERRED FROM THE TIMESTAMP, because a
# tile boundary is also seconds wide and the date fill below was wrong on four of
# five frames for exactly that reason. Over the ANALYSED WINDOW, a twin pair
# differs only where the icons were: measured on the 2026-09-12 set, 67 pairs at
# 0.51-2.0 % of the window in a median of 46 blobs of about 170 px, and nothing
# else. A pair that is not the same view differs on 33-89 % and is refused.
# Corroboration, independent of the pixels: across the 67 accepted pairs the two
# status-bar dates agree 52 times, have one side unread 15 times, and disagree 0.
TWIN_SECONDS = 60.0
TWIN_DIFF_TOL = 20          # per-channel difference that counts as a change
TWIN_MAX_DIFF_FRAC = 0.05   # icons are ~2 % of the window; terrain is ~35 % up
TWIN_MAX_BLOB_FRAC = 0.01   # and every icon is small — one big blob is terrain
# THE TIME SLIDER IS INSIDE THE ANALYSED WINDOW and it is not ground. Script
# 41's `_frame_window` opens at row 87 on these captures and the slider occupies
# roughly the next 35 rows at the left-hand end — the same widget that produced
# 42 worthless registrations when `_detect_markers` mistook it for control. Two
# twins of DIFFERENT timeline dates therefore differ there by construction:
# measured on 17-37-46 against 17-37-51, a single 14,851 px region at rows
# 87-121, which is 1.04 % of the window on its own and refused the pair at a
# total difference of 1.40 %. Skipped, with margin over the 35 rows measured.
TWIN_SKIP_TOP_PX = 48
_CAPTURE_TS = re.compile(r"(\d{4})-(\d{2})-(\d{2})[ _](\d{2})-(\d{2})-(\d{2})")


def _capture_time(name):
    m = _CAPTURE_TS.search(str(name))
    if not m:
        return None
    try:
        return pd.Timestamp(*(int(g) for g in m.groups()))
    except ValueError:
        return None


def _m41():
    spec = importlib.util.spec_from_file_location(
        "m41", str(REPO / "src" / "41_canopy_cover.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ── the status bar ─────────────────────────────────────────────────────────
_OCR = {"mod": None, "tried": False, "why": None, "runtime_warned": False}


def _ocr():
    """pytesseract AND the tesseract binary, proved ONCE, with the real reason.

    THERE ARE TWO WAYS THIS FAILS AND THEY NEED DIFFERENT FIXES. v1.0.0 checked
    only the first, and the second is the one that bit:

      the binding   `import pytesseract` fails. That is the D-155 venv/system
                    split - `check_all.sh` activates the venv, a bare `python3`
                    does not - and it is fixed with a pip install into the
                    interpreter actually in use.
      the BINARY    `pytesseract` imports, and the `tesseract` EXECUTABLE it
                    shells out to is missing, off PATH, or cannot find its
                    language data. Every `image_to_string` then raises, v1.0.0
                    swallowed that exception once per crop, and the run reported
                    `OCR saw ''` on every frame with no hint of the cause - 36
                    such lines in `working/updates/ingest_2026-09-12.txt`, and
                    not one of them says the word tesseract. Reproduced exactly
                    by running the same tree with the binary taken off PATH.

    The binding is a pip package; the binary is NOT, and installing the first
    does nothing for the second. So the binary is proved here by asking it for
    its version, and a failure names the executable it tried, the exception, and
    the system package to install. Printed ONCE, not per file.
    """
    if _OCR["tried"]:
        return _OCR["mod"]
    _OCR["tried"] = True
    try:
        import pytesseract                                    # noqa: PLC0415
    except ImportError:
        _OCR["why"] = "the pytesseract binding is not installed"
        warn(f"pytesseract is not importable by {sys.executable} - the "
             f"imagery date cannot be read from ANY frame.")
        warn("    it is a venv/system split (D-155): install it into the "
             "interpreter you are running, e.g.")
        warn(f"    {Path(sys.executable).parent / 'pip'} install pytesseract")
        return None
    cmd = str(getattr(pytesseract.pytesseract, "tesseract_cmd", "tesseract"))
    try:
        ver = pytesseract.get_tesseract_version()
    except Exception as exc:                                  # noqa: BLE001
        _OCR["why"] = f"the tesseract binary is unusable ({type(exc).__name__})"
        warn("the pytesseract binding imports, but the tesseract BINARY it "
             "calls is unusable - the imagery date cannot be read from ANY "
             "frame.")
        warn(f"    tried to run: {cmd!r}"
             f"{'' if shutil.which(cmd) else '   (not found on PATH)'}")
        warn(f"    {type(exc).__name__}: {_one_line(exc)}")
        warn("    the binding is a pip package and the binary is NOT - pip "
             "install cannot supply it. Install it system-wide:")
        warn("        sudo apt install tesseract-ocr")
        warn(f"    then re-check with: {sys.executable} "
             f"tools/ingest_capture.py --check-ocr")
        return None
    info(f"OCR ready: tesseract {ver} via pytesseract "
         f"{getattr(pytesseract, '__version__', '?')}, binary {cmd!r}")
    _OCR["mod"] = pytesseract
    return pytesseract


def _one_line(exc) -> str:
    s = str(exc).strip()
    return s.splitlines()[0][:160] if s else "(no message)"

def _otsu(arr) -> float:
    """A threshold from the crop's OWN histogram, for the bars over bright sand.

    A fixed threshold is a statement about the ground behind the text, and this
    bar is rendered over whatever the imagery happens to show. Otsu asks the
    crop instead.
    """
    v = arr.ravel()
    best, score = 150.0, 0.0
    for t in range(40, 240, 8):
        lo, hi = v[v <= t], v[v > t]
        if len(lo) < 10 or len(hi) < 10:
            continue
        s = len(lo) * len(hi) * (lo.mean() - hi.mean()) ** 2
        if s > score:
            best, score = float(t), s
    return best


_DATE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


def _candidates():
    """The imagery dates this site is KNOWN to have, from the manifest.

    Martin: "surely we can give it a range of dates to choose from" — and the
    range exists. Google Earth holds a fixed, small set of captures over
    Newborough, and `aerial_manifest.csv` already records them. That turns a
    free-text OCR problem into a choice among about fifteen, which is a far
    easier problem and a self-checking one.

    It is what rescues the digit misreads the voting could only discard:
    "3/81/2020" is one character from 3/31/2020, "9/44/2019" one from 9/11/2019,
    "4/26/2009" one from 4/20/2009. None of those is a valid date, so no amount
    of re-cropping recovers them; matching to the known set does.

    A capture whose date matches NOTHING in the set is reported as unrecognised
    rather than forced onto the nearest candidate — that is how a genuinely new
    imagery date announces itself, and it must not be silently absorbed.
    """
    try:
        man = pd.read_csv(MANIFEST, float_precision="round_trip")
        out = {str(d)[:10] for d in man["imagery_date"].dropna()}
    except Exception:                                         # noqa: BLE001
        out = set()
    # A date confirmed by hand is as known as one in the manifest, and is how a
    # timeline entry outside the enumerated set becomes matchable for the REST of
    # the series — 12/31/2009 and 12/31/2016 arrived exactly this way.
    out |= {d for d, _ in _hand_dates().values()}
    return sorted(d for d in out if len(d) == 10 and d[4] == "-")


def _hand_dates() -> dict:
    """{filename: (iso date, note)} from `capture_dates_by_hand.csv`, if present."""
    try:
        h = pd.read_csv(HAND_DATES, float_precision="round_trip")
    except Exception:                                         # noqa: BLE001
        return {}
    out = {}
    for _, r in h.iterrows():
        d = str(r["imagery_date"])[:10]
        if len(d) == 10 and d[4] == "-":
            out[str(r["file"])] = (d, str(r.get("note") or ""))
    return out


def _match_candidate(mm, dd, yy, cands):
    """(iso, distance) for the closest known imagery date, or (None, None).

    Distance is character edits between the OCR's own "M/D/YYYY" and each
    candidate rendered the same way, so a single misread digit costs 1.
    """
    if not cands:
        return None, None
    probe = f"{mm}/{dd}/{yy}"
    best, bd = None, 99
    for c in cands:
        y, m, d = int(c[:4]), int(c[5:7]), int(c[8:10])
        cand = f"{m}/{d}/{y}"
        if len(cand) != len(probe):
            dist = 9 if abs(len(cand) - len(probe)) > 1 else 3
        else:
            dist = sum(1 for x, y_ in zip(probe, cand) if x != y_)
        if dist < bd:
            best, bd = c, dist
    return best, bd
_LL = re.compile(r"(\d{1,3})[°o](\d{1,2})'([\d.]+)\"?\s*([NSEW])")
_ALT = re.compile(r"eye\s*alt\s*([\d.]+)\s*(km|m)", re.I)


def _raw_note(sb) -> str:
    """What the bar actually produced, but ONLY where no date was read.

    The docstring has always said the raw text is kept because it is the only
    way to tell a bad crop from a bad frame, and it was printed and then thrown
    away. An empty string here on every row is the signature of a broken
    tesseract; garbage text is the signature of a hard frame. That distinction
    is worth having in the file rather than in a terminal that has scrolled.
    """
    return "" if sb.get("date") else str(sb.get("ocr_raw") or "")[:70]


def _status_bar(path: Path) -> dict:
    """Imagery date, centre and eye altitude, from the rendered status bar.

    Every field is optional and a missing one is reported as missing. The bar is
    small, light text on a dark strip, so it is cropped, upscaled and read with
    `--psm 7` (one line); the raw text is kept for the report because it is the
    only way to tell a bad crop from a bad frame.
    """
    out = {"date": None, "date_source": None, "lat": None, "lon": None,
           "eye_alt_km": None, "ocr_raw": ""}
    pytesseract = _ocr()
    if pytesseract is None:
        return out
    a = Image.open(path).convert("L")
    w, h = a.size
    best = ""
    # THE BAR IS RIGHT-ALIGNED, SMALL, AND SITS OVER THE IMAGERY. Light text on
    # whatever the ground happens to be, so a plain crop reads it over dark
    # forest and fails over bright sand. Cropping tight to the right-hand end
    # and thresholding first took the read rate on the 2026-09-12 captures from
    # 40/80 to 64/80; no single threshold works over both sand and water.
    #
    # EVERY CROP IS TRIED AND THE VALID DATES VOTE. The first version stopped at
    # the first date-SHAPED match, which meant a misread like "3/81/2020" ended
    # the search and the frame was reported unreadable even though a wider crop
    # read it correctly — 11 of 20 where voting gets 17. A crop that is too
    # narrow also truncates "Imagery Date:" off the left on the wider bars, so
    # the cascade runs from tight to wide.
    votes, raws, unknown = {}, [], set()
    cands = _candidates()
    # THE CASCADE IS IN TWO HALVES AND THE SECOND HALF EXISTS BECAUSE OF THE
    # LIGHT-ON-LIGHT BARS. The fixed thresholds below read the bar wherever it
    # sits on dark ground, and they cannot read it at all where "Imagery Date"
    # falls over bright sand: binarising at 120-170 turns white text on a white
    # beach into a blank. Measured on the 2026-09-12 captures, five of the
    # twenty frames the fixed thresholds could not read carry a perfectly
    # legible date over sand, and an inverted-autocontrast or Otsu crop reads
    # all five - `5/26/2012` on three of them, which is a date NO neighbour
    # carries, so the pair-fill would have proposed the wrong one.
    #
    # (mode, x0, bar-height). A numeric mode is a fixed threshold; "otsu" picks
    # the threshold from the crop's own histogram; "inv" autocontrasts and
    # inverts, which is what rescues light text on light ground.
    for mode, x0, y0 in ((150, 0.62, 18), (150, 0.62, 22), (170, 0.55, 18),
                         (120, 0.62, 18), (150, 0.45, 18), (170, 0.45, 22),
                         (150, 0.35, 20), (0, 0.30, 20),
                         ("inv", 0.62, 26), ("inv", 0.45, 26),
                         ("inv", 0.30, 20), ("otsu", 0.30, 20),
                         ("otsu", 0.45, 20), ("otsu", 0.62, 20)):
        crop = a.crop((int(w * x0), h - y0, w, h))
        arr = np.asarray(crop).astype(float)
        if mode == "inv":
            crop = ImageOps.invert(ImageOps.autocontrast(crop, cutoff=1))
        elif mode == "otsu":
            crop = Image.fromarray(((arr > _otsu(arr)) * 255).astype("uint8"))
        elif mode:
            crop = Image.fromarray(((arr > mode) * 255).astype("uint8"))
        crop = crop.resize((crop.width * 4, y0 * 4), Image.LANCZOS)
        try:
            t = pytesseract.image_to_string(
                crop, config="--psm 7").strip().replace(chr(10), " ")
        except Exception as exc:                              # noqa: BLE001
            # The preflight has already proved the binary, so a failure HERE is
            # new - a crop tesseract will not take, or an environment that broke
            # mid-run. Silence is what made the v1.0.0 failure unreadable, so it
            # is said once and the run continues.
            if not _OCR["runtime_warned"]:
                _OCR["runtime_warned"] = True
                warn(f"  tesseract failed on a crop - {type(exc).__name__}: "
                     f"{_one_line(exc)}. Reported once; any frame whose crops "
                     f"all fail this way will have NO date.")
            continue
        raws.append(t)
        for m in _DATE.finditer(t):
            mm, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if not (2000 <= yy <= 2100):
                continue
            iso, dist = _match_candidate(mm, dd, yy, cands)
            if iso is not None and dist <= 2:
                # A known imagery date, exactly or within two misread
                # characters. Nearer matches vote more strongly.
                votes[iso] = votes.get(iso, 0) + (3 if dist == 0 else 1)
                continue
            try:
                iso = pd.Timestamp(yy, mm, dd).date().isoformat()
            except ValueError:
                continue                      # a digit misread, not a date
            unknown.add(iso)
        # TWO EXACT MATCHES TO THE SAME KNOWN DATE ARE ENOUGH. The cascade is
        # now fourteen crops and running all of them on every frame spends most
        # of the tool's time re-reading a bar that two independent crops have
        # already agreed on, character for character. The hard frames still get
        # the full cascade, because they never reach this.
        if any(v >= 6 for v in votes.values()):
            break
    # THE LONGEST TEXT IS NOT THE BEST TEXT. `best` is the string the
    # coordinates and the eye altitude are read from, and v1.0.0 took whichever
    # crop produced the most characters - which, on a thresholded crop of bright
    # sand, is the one that produced the most noise. Prefer the text that
    # actually matches the bar's own fields, and fall back to length.
    best = max(raws, key=lambda t: (len(_LL.findall(t)) + bool(_ALT.search(t)),
                                    len(t))) if raws else ""
    out["ocr_raw"] = best
    if votes:
        # The most-voted valid date; ties break to the earliest, which is
        # arbitrary but deterministic, and a tie is flagged for review anyway.
        top = max(sorted(votes), key=lambda k: votes[k])
        out["date"] = top
        out["date_source"] = "status bar"
        if unknown:
            warn(f"  note: the crops also produced {sorted(unknown)}, which is "
                 f"not a known imagery date for this site")
        if len(votes) > 1:
            warn(f"  the crops disagreed on the date {sorted(votes)} — took "
                 f"{top}; CHECK THIS ONE against the frame")
            out["date_source"] = "status bar (crops disagreed)"
        return out
    if unknown:
        # No known date matched, but something date-shaped and VALID was read.
        # That is either a new capture date or a bad read, and the tool cannot
        # tell which — so it says so and proposes nothing.
        warn(f"  read {sorted(unknown)}, which is NOT among the "
             f"{len(cands)} known imagery dates. Either this is a new date "
             f"— add it to the manifest — or the bar was misread.")
        return out
    d = _DATE.search(best)
    if d:
        mm, dd, yy = int(d.group(1)), int(d.group(2)), int(d.group(3))
        try:
            out["date"] = pd.Timestamp(yy, mm, dd).date().isoformat()
            out["date_source"] = "status bar"
        except ValueError:
            # A MISREAD, NOT A DATE. Seen on these captures: "3/81/2020" for
            # 3/31/2020 and "9/44/2019" for 9/11/2019. Reported, never coerced
            # into the nearest plausible day.
            warn(f"  status bar read as {d.group(0)}, which is not a date "
                 f"- a digit misread; enter it by hand")
    ll = _LL.findall(best)
    if len(ll) >= 2:
        def dec(g):
            v = float(g[0]) + float(g[1]) / 60 + float(g[2]) / 3600
            return -v if g[3] in ("S", "W") else v
        out["lat"], out["lon"] = dec(ll[0]), dec(ll[1])
    al = _ALT.search(best)
    if al:
        v = float(al.group(1))
        out["eye_alt_km"] = v if al.group(2).lower() == "km" else v / 1000.0
    return out


# ── locating the frame from its own control points ─────────────────────────
def _detect_rings(a, thr=RING_BRIGHT_SWEEP[0]):
    """The control points as Google Earth actually draws them: white rings.

    `georef_grid.kml` styles its placemarks as the blue pushpin, because that is
    what Script 41's `_detect_markers` keys on. Google Earth drew **white
    circles with a centre dot** instead (Martin, 2026-09-12), so the pushpin
    detector found no marker anywhere on the map and fell back on the only blue
    left in frame — the interface. On every one of 157 captures it returned the
    same 11 "markers" at rows 88-102, which is the time-slider widget, and
    matching that horizontal line to one ROW of a regular grid produced 42
    registrations that all looked plausible and were all worthless.

    A ring is a specific thing and easy to state: a BRIGHT, near-neutral blob,
    6-20 px square, roughly as tall as it is wide, that does NOT fill its own
    bounding box and whose centre is not bright. The last two conditions are
    what separate it from a sand patch, which is a filled blob of any shape.

    The returned point is the ring's CENTRE, not the bottom edge. A pushpin is a
    teardrop and points at its tip; a ring sits on its own centre. Taking the
    tip convention here would displace every control point by half an icon.

    Measured on the 2026-09-12 captures: 49-81 rings per frame spread across the
    full width and height, fitting the grid at about 1.0 m/px with residuals of
    0.8-1.3 m, against 2.884 m/px and 3.93 m for the committed series.
    """
    from scipy import ndimage                                 # noqa: PLC0415
    mx, mn = a.max(axis=2), a.min(axis=2)
    br = (mn > thr) & ((mx - mn) < RING_NEUTRAL)
    lab, n = ndimage.label(br)
    if n == 0:
        return np.zeros((0, 2), float)
    objs = ndimage.find_objects(lab)
    sz = ndimage.sum(br, lab, range(1, n + 1))
    out = []
    for k in range(n):
        if not (RING_MIN_PX < sz[k] < RING_MAX_PX):
            continue
        sy, sx = objs[k]
        h, w = sy.stop - sy.start, sx.stop - sx.start
        if not (RING_MIN_D <= h <= RING_MAX_D and RING_MIN_D <= w <= RING_MAX_D):
            continue
        if abs(h - w) > RING_SQUARENESS:
            continue
        if sz[k] / float(h * w) > RING_MAX_FILL:      # a disc, not a ring
            continue
        cy, cx = (sy.start + sy.stop) // 2, (sx.start + sx.stop) // 2
        if br[cy, cx]:                                # centre must be hollow
            continue
        out.append((float(cx), float(cy)))
    return np.asarray(out, float)


def _seed_transform(cx, cy, gsd, rot_deg, shape):
    """A north-up-plus-rotation affine, good enough to start the matcher."""
    th = np.radians(rot_deg)
    ct, st = np.cos(th), np.sin(th)
    h, w = shape

    def f(E, N, cx=cx, cy=cy, gsd=gsd, ct=ct, st=st, w=w, h=h):
        dx = (np.asarray(E, float) - cx) / gsd
        dy = (np.asarray(N, float) - cy) / gsd
        return (w / 2.0 + dx * ct + dy * st, h / 2.0 + dx * st - dy * ct)
    return f


def _locate(path: Path, m41, nets, sb, rot_step) -> dict:
    """Fit the frame to whichever control net registers it better."""
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    # DETECTION IS NOT RESTRICTED TO SCRIPT 41's ANALYSED WINDOW, and the
    # attempt is recorded here so it is not made again. On one 2026-09-12
    # capture, 54 of 101 detections sat in the bottom 10 % of the screen — the
    # attribution line, the scale bar, the overlays — so blanking outside
    # `_frame_window` looked like an obvious tightening. Measured, it LOST
    # registrations: `_frame_window` is the crop for the site viewpoint at
    # 3.70 km, and on a 1.0-2.3 km tile it cuts off real control, taking
    # 16-58-39 from 44 of 74 pins at 1.060 m/px north-up to 34 of 52 at
    # 2.373 m/px and heading 270. The interface detections cost the matcher work
    # and nothing else: they cannot match a 250 m lattice, and the fit discards
    # them. Excluding them wants the window of THIS capture geometry, which is
    # not a constant this tool owns.
    res = {"n_tips": 0, "n_matched": 0, "gsd_m": None,
           "residual_median_m": None, "net": None, "ring_thr": None,
           "heading_deg": None, "fitted": None, "shape": a.shape[:2]}
    best_net = None
    for thr in RING_BRIGHT_SWEEP:
        tips = _detect_rings(a, thr)
        res["n_tips"] = max(res["n_tips"], len(tips))
        if len(tips) < 8:
            continue
        for net_name, (E, N) in nets.items():
            r = _fit_one(tips, E, N, m41, sb, rot_step, res["shape"])
            if r is None:
                continue
            r["net"] = net_name
            r["ring_thr"] = thr
            r["n_tips"] = len(tips)
        # PREFER THE FIT WITH MORE CONTROL POINTS, not the lowest residual.
        # A homography can always be made to fit a handful of points closely,
        # and on these captures the rotation search kept finding 16-point
        # solutions at 2.9 m/px that scored a lower per-point residual than the
        # correct 44-point solution at 1.06 m/px. More points constrain more,
        # so matched count leads and the residual only breaks ties.
            if (best_net is None
                    or (r["n_matched"], -r["residual_median_m"])
                    > (best_net["n_matched"], -best_net["residual_median_m"])):
                best_net = r
        if (best_net is not None
                and best_net["n_matched"] >= RING_SWEEP_ENOUGH_POINTS
                and best_net["residual_px"] <= RING_SWEEP_ENOUGH_PX):
            break
    if best_net is None:
        return res
    res.update({k: best_net[k] for k in
                ("n_matched", "gsd_m", "residual_median_m", "heading_deg",
                 "fitted", "net", "ring_thr", "n_tips", "spread_ratio")})
    res["residual_px"] = best_net["residual_px"]
    return res


def _fit_one(tips, E, N, m41, sb, rot_step, shape):
    """One control net: seed, fit, sanity-check.

    THE SEED COMES FROM SCRIPT 41's OWN `_seed_from_wells`, not from a rotation
    search of my own. That routine scans pixels-per-metre and votes on the
    translation in a 2-D histogram, and it is the thing that solved this exact
    problem for the site captures, which carry no control outline — measured
    there at 39 of 88 markers within 10 px against 6 for the alternative. A
    hand-rolled search seeded from the net centroid registered nothing.

    The rotation search is kept as a FALLBACK, because `_seed_from_wells`
    assumes a north-up frame (it scans an axis-aligned scale, sx and sy) and a
    rotated capture breaks that assumption. So: try the project's routine first,
    and fall back to searching rotation when the capture is rotated.
    """
    # Seed centre: the control-net centroid is the only prior that needs no OCR.
    cx, cy = float(np.mean(E)), float(np.mean(N))
    res = {}
    alt = sb.get("eye_alt_km") or REF_ALT_KM
    gsd0 = REF_GSD_M * alt / REF_ALT_KM
    best = None
    # 1. the project's own seeder, for a north-up capture.
    try:
        s0 = m41._seed_from_wells(tips, E, N)
    except Exception:                                         # noqa: BLE001
        s0 = None
    if s0 is not None:
        try:
            pred, r, P, nn = m41._match_and_fit(
                tips, E, N, s0, (90.0, 60.0, 40.0, 25.0))
            if nn >= 8:
                best = (pred, r, P, nn, 0.0, gsd0)
        except Exception:                                     # noqa: BLE001
            pass
    # SKIP THE ROTATION SEARCH when the north-up seed already gave a
    # well-constrained fit. The search is 72 rotations x 3 scales x a full
    # match-and-fit, which is ~9 s a frame, and every capture in this series
    # comes back at heading 0 because Google Earth was never rotated. It stays
    # in the code for a rotated capture; it just is not paid for when the
    # cheaper seed has already answered.
    if best is not None and best[3] >= ROT_SKIP_POINTS \
            and np.median(best[1]) <= ROT_SKIP_PX:
        pred, r, P, n, rot, gs = best
    else:
            # 2. a rotation search, for a capture that is not north-up.
        for rot in np.arange(0, 360, rot_step):
            for gs in (gsd0 * 0.8, gsd0, gsd0 * 1.25):
                seed = _seed_transform(cx, cy, gs, rot, shape)
                try:
                    pred, r, P, n = m41._match_and_fit(
                        tips, E, N, seed, (90.0, 60.0, 40.0, 25.0))
                except Exception:                                 # noqa: BLE001
                    continue
                if n >= 8 and (best is None
                               or (n, -np.median(r)) > (best[3], -np.median(best[1]))):
                    best = (pred, r, P, n, rot, gs)
    if best is None:
        return None
    pred, r, P, n, rot, gs = best
    # The GSD implied by the fit, from the control points themselves.
    u, v = pred(E, N)
    d_px = np.hypot(np.diff(u), np.diff(v))
    d_m = np.hypot(np.diff(E), np.diff(N))
    ok = (d_px > 1) & (d_m > 1)
    res.update(n_matched=int(n), heading_deg=float(rot), fitted=pred,
               gsd_m=float(np.median(d_m[ok] / d_px[ok])) if ok.any() else None,
               residual_px=float(np.median(r)))
    res["residual_median_m"] = (res["residual_px"] * res["gsd_m"]
                                if res["gsd_m"] else None)
    # REFUSE a degenerate fit: matched points that lie on a line.
    q = P[:, 2:4].astype(float)
    q = q - q.mean(axis=0)
    sv = np.linalg.svd(q, compute_uv=False) if len(q) >= 3 else np.array([1.0, 0.0])
    ratio = float(sv[1] / sv[0]) if sv[0] > 0 else 0.0
    res["spread_ratio"] = ratio
    if ratio < MIN_SPREAD_RATIO:
        return None

    # REFUSE a fit that is not one. See MAX_RESIDUAL_PX and MIN/MAX_GSD_M.
    if res["residual_px"] > MAX_RESIDUAL_PX:
        return None
    if not res["gsd_m"] or not (MIN_GSD_M <= res["gsd_m"] <= MAX_GSD_M):
        return None
    if res["residual_median_m"] is None:
        return None
    return res


def _same_view(pa, pb, m41):
    """Do two captures show the same ground, over the analysed window?

    Returns the differing fraction, the largest connected difference as a
    fraction, and the blob count — or None if the two cannot be compared. The
    caller decides; see TWIN_MAX_DIFF_FRAC.

    The window is Script 41's own `_frame_window`, not the whole screen: the
    status bar carries the imagery date, which differs BETWEEN twins of
    different tiles and would swamp the comparison, and the bottom strip carries
    the attribution and the scale bar.
    """
    from scipy import ndimage                                 # noqa: PLC0415
    try:
        a = np.asarray(Image.open(pa).convert("RGB")).astype(np.int16)
        b = np.asarray(Image.open(pb).convert("RGB")).astype(np.int16)
    except Exception:                                         # noqa: BLE001
        return None
    if a.shape != b.shape:
        return None
    r0, r1, c0, c1 = m41._frame_window(a.shape[0], a.shape[1])
    r0 = min(r0 + TWIN_SKIP_TOP_PX, r1)          # the time slider is not ground
    d = (np.abs(a[r0:r1, c0:c1] - b[r0:r1, c0:c1]).max(axis=2) > TWIN_DIFF_TOL)
    if d.size == 0:
        return None
    lab, n = ndimage.label(d)
    mx = (float(ndimage.sum(d, lab, range(1, n + 1)).max()) / d.size) if n else 0.0
    return {"diff_frac": float(d.mean()), "max_blob_frac": mx, "n_blobs": int(n)}


def _twin_fill(rows, paths, m41) -> None:
    """Give every unregistered frame its twin's transform, where the pixels
    license it. Mutates `rows`. See the TWIN_* constants for the reasoning.

    A frame filled this way is marked `locate_source`, so the CSV never
    presents an inherited transform as a fit of its own.
    """
    reg = [i for i, r in enumerate(rows) if r.get("gsd_m")]
    if not reg:
        return
    n_ok = n_no = 0
    for i, r in enumerate(rows):
        if r.get("gsd_m"):
            continue
        t = _capture_time(r["file"])
        pa = paths.get(r["file"])
        if t is None or pa is None:
            continue
        best = None
        for j in reg:
            u = _capture_time(rows[j]["file"])
            pb = paths.get(rows[j]["file"])
            if u is None or pb is None:
                continue
            if abs((t - u).total_seconds()) > TWIN_SECONDS:
                continue
            m = _same_view(pa, pb, m41)
            if m is None:
                continue
            k = (m["diff_frac"], m["max_blob_frac"])
            if best is None or k < best[0]:
                best = (k, j, m)
        if best is None:
            continue
        (df, mb), j, m = best
        src = rows[j]
        if df > TWIN_MAX_DIFF_FRAC or mb > TWIN_MAX_BLOB_FRAC:
            warn(f"  {r['file']}: nearest registered capture "
                 f"{src['file']} differs on {df * 100:.1f} % of the window "
                 f"(largest single region {mb * 100:.2f} %) — a DIFFERENT VIEW, "
                 f"not its twin. Left unlocated.")
            r["verdict"] = "NO FIT - NO TWIN"
            n_no += 1
            continue
        for k in ("gsd_m", "residual_median_m", "heading_deg", "n_matched",
                  "control_net"):
            r[k] = src.get(k)
        r["locate_source"] = src["file"]
        r["twin_diff_pct"] = round(df * 100, 3)
        r["twin_blobs"] = m["n_blobs"]
        r["verdict"] = "REVIEW"
        # The twin's date is stronger evidence than the neighbour agreement the
        # date fill uses, because the ground has been measured identical.
        if not r.get("date") and src.get("date"):
            r["date"] = src["date"]
            r["date_source"] = f"markers-ON twin {src['file']}"
        info(f"  {r['file']}: located from its twin {src['file']} — the window "
             f"differs on {df * 100:.2f} % in {m['n_blobs']} blob(s), which is "
             f"the control icons; {src.get('gsd_m', 0):.3f} m/px inherited")
        n_ok += 1
    step(f"twin fill: {n_ok} frame(s) located from a markers-ON twin, "
         f"{n_no} refused as a different view")


# ── does it duplicate anything already in the series? ──────────────────────
def _warren_mask(m41, fitted, shape, date):
    from PIL import ImageDraw                                 # noqa: PLC0415
    geom = warren_on(date)
    img = Image.new("1", (shape[1], shape[0]), 0)
    dr = ImageDraw.Draw(img)
    polys = (list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom])
    for poly in polys:
        cc = list(poly.exterior.coords)[:-1]
        xs, ys = fitted([c[0] for c in cc], [c[1] for c in cc])
        dr.polygon(list(zip(np.asarray(xs), np.asarray(ys))), fill=1)
    W = np.array(img, dtype=bool)
    r0, r1, c0, c1 = m41._frame_window(shape[0], shape[1])
    W[:r0] = False
    W[r1:] = False
    W[:, :c0] = False
    W[:, c1:] = False
    return W


def _duplicates(path, m41, W):
    """Share of warren pixels IDENTICAL to each existing frame of the same size."""
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.int16)
    man = pd.read_csv(MANIFEST, float_precision="round_trip")
    out = []
    tot = int(W.sum())
    if not tot:
        return out
    for _, r in man.iterrows():
        q = DATA_GEO_DIR / str(r["filename"])
        if not q.exists() or q.resolve() == Path(path).resolve():
            continue
        try:
            b = np.asarray(Image.open(q).convert("RGB")).astype(np.int16)
        except Exception:                                     # noqa: BLE001
            continue
        if b.shape != a.shape:
            continue
        f = float(((np.abs(a - b).max(axis=2) <= IDENTICAL_TOL) & W).sum()) / tot
        if f > DUP_REPORT_FRAC:
            out.append((f, str(r["imagery_date"]), str(r["filename"])))
    return sorted(out, reverse=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--check-ocr", action="store_true",
                    help="test the OCR chain for THIS interpreter and exit")
    ap.add_argument("--rot-step", type=float, default=5.0,
                    help="rotation search step in degrees for the seed")
    a = ap.parse_args()
    banner("Capture ingest — proposes, never files", __version__)
    if a.check_ocr:
        # The whole cause of the 2026-09-12 zero-read run, in one command, with
        # no 157-frame run needed to discover it.
        info(f"interpreter: {sys.executable}")
        ok = _ocr() is not None
        step("OCR chain is READY" if ok
             else f"OCR chain is NOT available: {_OCR['why']}")
        return 0 if ok else 1
    if not a.paths:
        warn("give at least one file or directory, or --check-ocr")
        return 1

    if not GRID_CSV.exists():
        warn(f"{GRID_CSV.name} is missing; run tools/make_georef_kml.py first")
        return 1
    grid = pd.read_csv(GRID_CSV, float_precision="round_trip")
    nets = {"georef": (grid["easting"].values, grid["northing"].values)}
    info(f"control net: {len(grid)} point(s) from {GRID_CSV.name}")
    # THE OLD FRAMES CARRY THE DIPWELL PLACEMARKS, NOT THIS GRID, so both nets
    # are offered and the better fit wins. Without this the tool only works on
    # captures made after 2026-09-12, and cannot be tested against the series it
    # is meant to extend.
    try:
        from utils.paths import INT_LOCATIONS                 # noqa: PLC0415
        w = pd.read_csv(INT_LOCATIONS, float_precision="round_trip")
        ec = next(x for x in w.columns if x.lower() in ("easting", "e", "x"))
        nc = next(x for x in w.columns if x.lower() in ("northing", "n", "y"))
        nets["dipwells"] = (w[ec].values.astype(float),
                            w[nc].values.astype(float))
        info(f"           {len(w)} dipwell placemark(s), for the older frames")
    except Exception:                                         # noqa: BLE001
        pass
    m41 = _m41()
    hand = _hand_dates()
    if hand:
        info(f"{len(hand)} date(s) read by hand from {HAND_DATES.name}; these "
             f"override the bar and join the candidate set")
    else:
        info(f"no {HAND_DATES.name}; every date comes from the bar")

    files = []
    for p in a.paths:
        q = Path(p)
        files += sorted(q.glob("*.png")) if q.is_dir() else [q]
    info(f"{len(files)} capture(s) to read")

    rows = []
    for f in files:
        step(f"{f.name}")
        sb = _status_bar(f)
        hd = hand.get(f.name)
        if hd:
            was = sb["date"]
            sb["date"] = hd[0]
            sb["date_source"] = "read by hand" + (
                f" (OVERRIDES the bar, which read {was})" if was and was != hd[0]
                else "")
            if was and was != hd[0]:
                warn(f"  the bar reads {was}; the hand register says {hd[0]} "
                     f"and wins — {hd[1][:110]}")
        if sb["date"]:
            info(f"  imagery date {sb['date']} (status bar)")
        else:
            why = (f"{_OCR['why']} — see the warning above"
                   if _OCR["mod"] is None
                   else f"OCR saw {sb['ocr_raw'][:70]!r}")
            warn(f"  IMAGERY DATE NOT READ — enter it by hand; {why}")
        loc = _locate(f, m41, nets, sb, a.rot_step)
        if loc["n_tips"] == 0:
            # NOT A FAILURE. A measurement frame is captured with the markers
            # OFF so the ground is clean, which is the whole point of the twin
            # discipline — it cannot self-locate and does not need to. It takes
            # its twin's transform, which is exact: the 2021-03-24 ON/OFF pair
            # align at (0,0) px, r = 0.9954.
            info("  no control rings in this frame — either the control net "
                 "was switched off, or this is a clean measurement frame that "
                 "locates from its twin")
            rows.append({"file": f.name, "date": sb["date"],
                         "date_source": sb["date_source"],
                         "ocr_raw": _raw_note(sb),
                         "verdict": "MARKERS-OFF (locate from its twin)"})
            continue
        if loc["fitted"] is None:
            warn(f"  DID NOT REGISTER: {loc['n_tips']} ring(s) detected, no fit "
                 f"within {MAX_RESIDUAL_PX:.0f} px on any control net. Is the "
                 f"control net switched on, and the graticule OFF?")
            rows.append({"file": f.name, "date": sb["date"],
                         "date_source": sb["date_source"],
                         "ocr_raw": _raw_note(sb), "verdict": "NO FIT",
                         "n_tips": loc["n_tips"]})
            continue
        info(f"  registered on the {loc['net']} net, {loc['n_matched']} of "
             f"{loc['n_tips']} pin(s): {loc['gsd_m']:.3f} m/px, median residual "
             f"{loc['residual_median_m']:.2f} m ({loc['residual_px']:.2f} px), "
             f"heading about {loc['heading_deg']:.0f} deg, spread "
             f"{loc.get('spread_ratio', float('nan')):.2f})")
        info("  (an identification fit, not the production one — Script 41 "
             "still does that, and does it better)")
        dups = []
        if sb["date"]:
            W = _warren_mask(m41, loc["fitted"], loc["shape"], sb["date"])
            dups = _duplicates(f, m41, W)
            if dups:
                warn("  SHARES GROUND WITH AN EXISTING FRAME — a timeline entry "
                     "is a composite, not a capture:")
                for fr, d, n in dups[:5]:
                    warn(f"    {fr * 100:5.1f} % of the warren identical to "
                         f"{d}  {n}")
            else:
                info("  no existing frame shares more than "
                     f"{DUP_REPORT_FRAC * 100:.1f} % of the warren")
        # THE PREFIX IS THE VIEWPOINT'S AND THIS TOOL DOES NOT KNOW IT.
        # Measured on the first run: a vp3 `seabed` frame was proposed as
        # `site22-4-2017.png`, because the date is all the tool can see. The
        # date part is proposed; the prefix is left for whoever assigns the
        # viewpoint, which is a judgement about what the frame is FOR.
        name = "?"
        if sb["date"]:
            d = pd.Timestamp(sb["date"])
            name = f"<viewpoint-prefix>{d.day}-{d.month}-{d.year}.png"
        rows.append({
            "file": f.name, "date": sb["date"],
            "date_source": sb["date_source"], "ocr_raw": _raw_note(sb),
            "proposed_filename": name,
            "gsd_m": loc["gsd_m"], "residual_median_m": loc["residual_median_m"],
            "heading_deg": loc["heading_deg"], "n_matched": loc["n_matched"],
            "control_net": loc["net"],
            "max_share_with_existing": (dups[0][0] if dups else 0.0),
            "shares_with": (dups[0][1] if dups else ""),
            "verdict": "REVIEW" if (dups or not sb["date"]) else "OK",
        })
        info(f"  proposed name: {name}  (markers-ON twin: "
             f"{name.replace('.png', 'm.png')}) — the prefix is the "
             f"viewpoint's, and is yours to set")

    # A frame with no fit of its own takes its markers-ON twin's transform,
    # where the pixels license it. This runs BEFORE the date fill because a
    # measured-identical twin is stronger evidence of the date than two
    # neighbours agreeing, and it settles most of what the date fill would
    # otherwise have to guess at.
    _twin_fill(rows, {f.name: f for f in files}, m41)

    # PAIR FILL, AND WHY IT NOW REFUSES MOST OF THE TIME. The captures come off
    # the camera in bursts - a markers-ON and a markers-OFF of the same view
    # seconds apart, then the next tile - so a file whose bar will not read sits
    # between two that did, and taking its neighbour's date looks safe.
    #
    # IT IS NOT, AND THE FRAMES THEMSELVES PROVED IT. v1.0.0's docstring said
    # the date was taken "where BOTH neighbours read the SAME date"; the code
    # took the NEARER neighbour, agreement or not. Measured on the 2026-09-12
    # set: of the twenty frames it filled, thirteen sat on a boundary between
    # two different imagery dates, and of the five whose true date was later
    # recovered from the pixels, the fill had been WRONG on four. The frames
    # whose bar fails are disproportionately the ones at a date change, which is
    # exactly where a neighbour's date is least likely to be theirs.
    #
    # So the documented rule is now the implemented one: BOTH neighbours must be
    # within PAIR_SECONDS and must agree. Anything else is reported as
    # undetermined, with the candidates named, because on this evidence the
    # alternative is a coin flip wearing a provenance label.
    for i, r in enumerate(rows):
        if r.get("date"):
            continue
        t = _capture_time(r["file"])
        near = []
        for j in (i - 1, i + 1):
            if not (0 <= j < len(rows)) or not rows[j].get("date"):
                continue
            u = _capture_time(rows[j]["file"])
            if t is None or u is None:
                continue
            g = abs((t - u).total_seconds())
            if g <= PAIR_SECONDS:
                near.append((rows[j]["date"], g))
        agreed = {x[0] for x in near}
        if len(near) == 2 and len(agreed) == 1:
            r["date"] = near[0][0]
            r["date_source"] = ("adjacent captures agree "
                                f"({max(x[1] for x in near):.0f} s)")
            r["verdict"] = "REVIEW"
        elif near:
            r["date_source"] = "UNDETERMINED - neighbours " + ", ".join(
                f"{dte} ({g:.0f} s)" for dte, g in near)
            r["verdict"] = "REVIEW - DATE BY HAND"
            warn(f"  {r['file']}: no date in the bar and the neighbours do "
                 f"not settle it - "
                 + ", ".join(f'{dte} ({g:.0f} s)' for dte, g in near)
                 + " - read this one from the frame")
        else:
            r["date_source"] = "UNDETERMINED - no capture within "
            r["date_source"] += f"{PAIR_SECONDS:.0f} s carries a date"
            r["verdict"] = "REVIEW - DATE BY HAND"

    n_bar = sum(1 for r in rows if r.get("date_source") == "status bar")
    n_bar += sum(1 for r in rows
                 if str(r.get("date_source") or "").startswith("status bar ("))
    n_ord = sum(1 for r in rows
                if str(r.get("date_source") or "").startswith("adjacent"))
    n_non = sum(1 for r in rows if not r.get("date"))
    step(f"dates: {n_bar} read from the status bar, {n_ord} inferred from "
         f"agreeing adjacent captures (REVIEW), {n_non} not determined "
         f"(read those from the frame - the CSV names the candidates)")

    n_fit = sum(1 for r in rows if r.get("gsd_m") and not r.get("locate_source"))
    n_twin = sum(1 for r in rows if r.get("locate_source"))
    n_lost = len(rows) - n_fit - n_twin
    step(f"located: {n_fit} registered on a control net, {n_twin} inherited "
         f"from a markers-ON twin, {n_lost} not located")

    if rows:
        p = OUT / "ingest_proposals.csv"
        pd.DataFrame(rows).to_csv(p, index=False)
        saved(p.name)
    info("NOTHING HAS BEEN WRITTEN TO data/geo/. Confirm each row, then add it "
         "to aerial_manifest.csv by hand — including the attribution, which is "
         "a rights statement and is read from the image, not proposed here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
