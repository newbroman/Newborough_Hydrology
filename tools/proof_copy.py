#!/usr/bin/env python3
"""
proof_copy.py — the chapter you are reading, with every number's provenance
painted on it.

WHY
  Every numeric check in this corpus runs VALUE-FIRST: it takes what the pipeline
  publishes and asks whether the documents quote it. That direction has a blind
  spot which cost report12 a wrong headline for a month (changelog 2026-09-20c)
  and let three passages of report9 sit six weeks behind the pipeline (20e): a
  number that matches NO committed value — because it is wrong, or because its
  quantity was never registered — is invisible to a checker that finds citations
  by recognising the right one.

  This tool runs DOCUMENT-FIRST and SOURCE-FIRST. It takes one chapter, walks every
  number in reading order, works out which files that section draws on, and asks
  of each number: is it in THOSE files, and does it still agree? "It should be
  obvious from the text where the source of the numbers is" (Martin, 2026-09-20):
  §4.1.1 is the climate record, so its numbers come from the climate data and
  Scripts 00/01 and nowhere else — a match to a scrape-equilibrium slope in Script
  09c is a coincidence, not a citation, however exact.

WHERE A SECTION'S SOURCES COME FROM
  1. tools/proof_scope.csv — an editable map: document, section prefix, sources.
     A row here is authoritative for its section and its subsections. Add a row
     when the tool guesses wrong; that is the intended way to teach it.
  2. what the section itself declares: "(Source: …)" under its exhibits,
     "Script NN" in its prose, "Figure N" / "Table N" resolved through
     tools/figure_table_manifest.csv. A subsection inherits its parent's.
  A section with neither is checked against everything, as before.

WHAT THE COLOURS MEAN
  traced      green   equals a REGISTERED committed value (report_numbers files,
                      the value tables cite_check knows) from a file in the
                      section's sources, with the value's anchor beside it — or a
                      confirmed citation-index row points here and agrees.
  deep        teal    equals a cell, or a column's min/max/median/mean, or a
                      12-month rolling-mean extreme, in a committed CSV from the
                      section's sources that is in NO value table. Consistent with
                      the pipeline; nothing gates it; the tooltip names the file
                      to register.
  rounding    pale    one unit of the last quoted digit off — "fix a number when it
                      MOVES, not when it rounds differently" (2026-09-02).
  stale       amber   a confirmed index row points here and the value has moved,
                      or a "p < x" bound is contradicted by the row it belongs to.
  elsewhere   orange  equals something only OUTSIDE the section's sources. Either
                      the passage is stale or the section does not declare the file
                      it used. The signature of a stale passage.
  untraced    red     matches nothing in scope and nothing anchored anywhere.
  count       grey    a small whole number with nothing to check against.
  Statistics quoted together — a slope, its R², its p — are expected from ONE
  row: when a sentence's numbers resolve to the same file and row the tooltip
  says so, and a "p < 0.001" is checked against that row's p-value rather than
  ignored as a bound.

  A green mark is "a committed value with the right anchor, from the right
  file, sits here" — not a proof the sentence means it. Hover to see which.

CORRECTIONS — click a number
  Every painted number is clickable: say what it should read and why, and it joins
  a queue. Served through `python3 tools/proof_serve.py` (stdlib, one command, then
  open http://127.0.0.1:8765/report9.html) the queue is written to
  scratch/proof/corrections.jsonl, which a session reads with
  `python3 tools/proof_corrections.py --list` and works through in a batch. Opened
  as a file:// the queue is held in the browser and "copy for chat" gives a block
  to paste. Nothing is applied until a session verifies it against the CSVs.

WHAT IT WRITES
  scratch/proof/<doc>.html, <doc>_untraced.csv (red, amber and orange: the work
  list) and index.html. Not a gate. Reuses cite_check's value map, anchors and
  locator so it cannot disagree with the gate about what is committed.

Usage:
    python3 tools/proof_copy.py report9
    python3 tools/proof_copy.py report10 --section 5.2
    python3 tools/proof_copy.py Paper1 --list
    python3 tools/proof_copy.py report9 --no-deep      # registered values only, ~5 s faster
"""
from __future__ import annotations

__version__ = "1.8.0"  # Hollingham (2026) — 2026-09-20. From the third artifact queue:
#   a quantity letter gates its candidates ("p = 0.25" is a probability, not a
#   slope; "n =", "r =", "R² =", "k =" likewise); a p with no gated candidate is
#   checked against the p of the row its neighbours cite; well counts are derived
#   from the 01_wells_* column sets (88 = 66 reference + 22 extended; the lake is
#   not a well); k is the number of distinct clusters in Script 02's membership
#   CSV; polygon areas of data/geo/*.kml are candidates in hectares (the 8.4 ha
#   clearfell traces to nothing — the KML polygon is 4.4 ha).
# v1.7.0  2026-09-20. From the first artifact queue:
#   identifiers (ORCID, DOI) are not numbers; "n of N" takes N from n's file;
#   threshold differences (SD16 − SD15b = 37 cm) are derived values; each span
#   carries its section and the pasted block names doc and section.
# v1.6.0  2026-09-20. Portable: --bundle writes one
#   page with every chapter; published as a claude.ai artifact with the db
#   capability, the queue lives in the artifact store (third transport) and a
#   session reads it with ArtifactData — no laptop, no Wi-Fi.
# v1.5.0  2026-09-20. Reactive: click a number,
#   queue a correction; served by proof_serve.py the queue lands in
#   scratch/proof/corrections.jsonl, otherwise it is held in the browser and
#   copied for chat. proof_corrections.py lists and closes the queue.
# v1.4.0  2026-09-20. Source-first: a section's
#   scope (tools/proof_scope.csv, then what it declares) filters EVERY tier,
#   registered values included — "+0.014 °C yr⁻¹" in the climate record had been
#   painted green against Script 09c's scrape-equilibration slope. Row coherence:
#   a sentence's statistics are expected from one row, and "p < 0.001" is checked
#   against that row's p. Rolling-mean extremes are pseudo-cells (Martin: "the 50
#   must be the min of the PET rolling mean").
# v1.3.0  2026-09-20. Declared sources searched first; ELSEWHERE class.
# v1.2.0  2026-09-20. Unit forms need their unit; derived column statistics.
# v1.1.0  2026-09-20. Second tier over every CSV under outputs/ and data/.
# v1.0.0  2026-09-20. Written the day report12 was found quoting +0.53 for 0.82.

import argparse
import bisect
import csv
import html
import pathlib
import re
import sys
from collections import defaultdict, namedtuple

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import cite_check as cc  # noqa: E402  the authoritative value map and anchors

OUT_DIR = REPO / "scratch" / "proof"
SECTION_MAP = REPO / "tools" / "section_map.csv"
SCOPE_FILE = REPO / "tools" / "proof_scope.csv"
MANIFEST = REPO / "tools" / "figure_table_manifest.csv"

def resolve_doc(name: str) -> pathlib.Path:
    """`report9` -> report_edits/text/report9.md; `Paper1` -> docs/.../Paper1.md."""
    p = pathlib.Path(name)
    if p.exists():
        return p.resolve()
    cands = [q for g in ("report_edits/text/*.md", "docs/**/text/*.md")
             for q in REPO.glob(g) if q.stem.lower() == name.lower()]
    if not cands:
        cands = [q for g in ("report_edits/text/*.md", "docs/**/text/*.md")
                 for q in REPO.glob(g) if name.lower() in q.stem.lower()]
    if len(cands) != 1:
        sys.exit(f"cannot resolve {name!r}: {[str(c.relative_to(REPO)) for c in cands]}")
    return cands[0]


def _window(text: str, start: int, end: int, n: int = cc.ANCHOR_WINDOW) -> str:
    return text[max(0, start - n): end + n].lower()


# Key tokens whose written form in the documents is a glyph, which
# cite_check.anchor_groups() cannot see: a key spelt delta0 anchors on δ₀.
GLYPH_FORMS = {
    "delta0": ["δ₀", "δ0", "delta0", "shoreline amplitude", "decay amplitude"],
    "delta_0": ["δ₀", "δ0"], "lambda": ["λ", "reach"], "tau": ["τ"],
    "kappa": ["κ", "depth-coupling", "depth coupling"], "gamma": ["γ"],
    "dnse": ["δnse", "δ nse", "nse"], "nse": ["nse", "nash"],
    "halflife": ["t½", "half-life", "half life"], "t_half": ["t½", "half-life"],
    "thalf": ["t½", "half-life"], "vif": ["variance inflation", "vif"],
    "rmse": ["rmse"], "r2": ["r²", "r2"], "lcg": ["l_cg", "reach"],
    "cwb": ["cwb", "cumulative water balance"], "msl5": ["msl5", "spring level"],
    "pflood": ["p_flood", "p\\_flood", "flood"], "sy": ["specific yield", "sy"],
    "amp": ["amplif"], "amplification": ["amplif"], "slope": ["slope", "trend", "decline"],
    "closure": ["clos"], "residual": ["residual"], "interception": ["intercept"],
}


# Words that anchor nothing: they sit in every paragraph of a hydrology report.
WEAK_ANCHORS = {"month", "months", "year", "years", "annual", "daily", "water", "level",
                "levels", "table", "record", "records", "period", "window", "index",
                "gap", "full", "mean", "median", "total", "start", "end", "site"}


_ANCHOR_CACHE: dict = {}

# A cluster is named three ways in the prose — "C2", "Dune", "the Dune cluster" —
# and cite_check's key stop-list drops the label words, so "25 mm … Dune" could not
# anchor on `C2 (Dune) · LCSC_percent` (Martin, 2026-09-20: "all the numbers in
# this sentence, like the 28 mm, should have the same LCSC source").
CLUSTER_NAMES = {
    "c1": ["c1", "lake edge", "lake-edge"], "c2": ["c2", "dune cluster", "the dune", "c2 dune", "dune"],
    "c3": ["c3", "western residual", "western"], "c4": ["c4", "main forest", "forest interior", "plantation"],
    "c5": ["c5", "coastal forest", "plantation"],
}


def _cluster_subjects(label: str) -> list[str]:
    out = []
    for m in re.finditer(r"(?i)\bc([1-5])\b", label):
        out.extend(CLUSTER_NAMES["c" + m.group(1)])
    return out


def _anchor_sets(label: str):
    """(subject anchors, quantity anchors) for a registered key, cached: the same
    few thousand keys are asked about tens of thousands of times per chapter."""
    if label not in _ANCHOR_CACHE:
        subj, quant = cc.anchor_groups(label)
        quant = [q for q in quant if q.lower() not in WEAK_ANCHORS]
        for t in re.split(r"[_\W]+", label):
            if t and t.lower() in GLYPH_FORMS:
                quant.extend(GLYPH_FORMS[t.lower()])
        subj = subj + _cluster_subjects(label)
        _ANCHOR_CACHE[label] = ([k.lower() for k in subj], [k.lower() for k in quant])
    return _ANCHOR_CACHE[label]


def anchored_here(text: str, start: int, end: int, label: str,
                  strict: bool = False, w: str | None = None) -> bool:
    """cite_check.anchored(), evaluated at ONE span instead of every occurrence,
    with the glyph forms above added to the quantity anchors."""
    if label in cc.ANCHOR_PHRASES:
        pw = text[max(0, start - cc.PHRASE_WINDOW): end + cc.PHRASE_WINDOW].lower()
        n = text[start:end]
        return any(ph.replace("{n}", n).lower() in pw for ph in cc.ANCHOR_PHRASES[label])
    subj, quant = _anchor_sets(label)
    if not subj and not quant:
        # cite_check lets a key with no usable anchor match anywhere. For a
        # STRONG rendering that is tolerable; for a weak one (two digits) it
        # made every list marker "1." a citation of some 1.0 constant.
        return not strict
    if w is None:
        w = _window(text, start, end)
    if strict and subj and quant:
        return any(k in w for k in subj) and any(k in w for k in quant)
    return any(k in w for k in subj) or any(k in w for k in quant)


# ---------------------------------------------------------------------------
# one candidate index over every tier
# ---------------------------------------------------------------------------
# tier: "reg"  a registered value (cite_check.collect_values); anchors is None
#              and anchored_here(label) decides
#       "cell" a cell of a committed CSV; anchors = row label + column + file words
#       "stat" min/max/median/mean of a column; anchors = column words + stat words
#       "roll" min/max of a 12-month rolling mean of a monthly series
Cand = namedtuple("Cand", "rel label col value anchors form tier")
# anchors: {"label": [...], "col": [...], "file": [...], "stat": [...], "roll": [...]} for the
# CSV tiers; None for the registered tier, which anchors on its key through anchored_here().
ROWS: dict[tuple, dict] = {}          # (rel, row label) -> {column: value}, for p-bounds
REG_FILES: set[str] = set()           # files whose values cite_check registers

DPS = (0, 1, 2, 3, 4)
DEEP_ROOTS = ("outputs", "data")
DEEP_MAX_ROWS = 1200          # RAF_Valley_Climate.csv is 1,143 rows and is wanted
DEEP_MAX_BYTES = 400_000
_DEEP_STOP = cc._STOPWORDS | {"value", "values", "name", "label", "id", "index",
                              "unit", "note", "csv", "report", "numbers", "data"}
_MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august",
           "september", "october", "november", "december"]
STAT_WORDS = {"min": ["ranging from", "from", "shortest", "minimum", "lowest", "smallest", "least", "driest", "as low as"],
              "max": [" to ", "longest", "maximum", "highest", "largest", "up to", "wettest", "peak", "peaks"],
              "median": ["median"], "mean": ["mean", "average"]}
ROLL_WORDS = ["rolling", "12-month", "12 month", "moving"]


def _norm_num(s: str) -> str:
    s = re.sub(cc._MINUS_CLASS, "-", s)
    return s[1:] if s.startswith("+") else s


def _dp_of(s: str) -> int:
    return len(s.split(".")[1]) if "." in s else 0


def _deep_words(x) -> list[str]:
    out = []
    for w in re.split(r"[^A-Za-z0-9²½₀₁₂₃βδλκτ]+", str(x)):
        if len(w) >= 3 and w.lower() not in _DEEP_STOP and not w.isdigit():
            out.append(w.lower())
    return out


LABEL_SYNONYMS = {
    "squared": ["r²", "r2", "r-squared"], "rsq": ["r²", "r2"], "r2": ["r²", "r2"],
    "slope": ["slope", "trend", "yr⁻¹", "per year"], "intercept": ["intercept"],
    "pvalue": ["p =", "p<", "p \\<", "p ="], "p_value": ["p =", "p<", "p \\<"],
    "mean": ["mean", "average"], "median": ["median"], "total": ["total"],
    "anomaly": ["anomaly", "above"], "pre": ["pre-", "before"], "post": ["post-", "since", "after"],
    "long": ["long-term", "long term"], "term": ["long-term", "long term"],
    "peak": ["peak", "peaks", "highest"], "min": ["minimum", "lowest", "driest"], "max": ["maximum", "highest", "wettest"],
    "winter": ["winter"], "summer": ["summer"], "spring": ["spring"], "autumn": ["autumn"],
}
COLUMN_SYNONYMS = {
    "p": ["rain", "rainfall", "precipitation"], "rain": ["rain", "rainfall", "precipitation"],
    "pet": ["pet", "evapotranspiration", "evaporative"], "temp": ["temperature", "°c"],
    "tmax": ["maximum temperature", "°c"], "months": ["months"], "n": ["n ="],
    "min": ["minimum", "minima", "min"], "max": ["maximum", "maxima", "max"],
    "wl": ["water level", "water-level", "water table"], "amplitude": ["amplitude"],
    "mean": ["mean", "average"], "median": ["median"], "std": ["standard deviation", "sd"],
}
# a column's own words are informative even when they are generic elsewhere:
# "Mean_Summer_Min_m" anchors on mean, summer and minimum; the row stop-list is
# cite_check's, which drops all three.
_COL_STOP = {"value", "values", "name", "label", "id", "unit", "note", "csv", "data", "index", "col", "pct"}


def _label_anchors(lab: str) -> list[str]:
    lab = str(lab).strip()
    if re.fullmatch(r"\d{1,2}(\.0)?", lab) and 1 <= int(float(lab)) <= 12:
        mo = _MONTHS[int(float(lab)) - 1]
        return [mo, mo[:3]]                      # a month-numbered climatology row
    m = re.match(r"^(\d{4})-(\d{2})(?:-\d{2})?$", lab)
    if m:
        y, mo = m.group(1), int(m.group(2))
        # month AND year: a bare year sits in every paragraph of a 21-year record
        return [f"{_MONTHS[mo-1][:3]} {y}", f"{_MONTHS[mo-1]} {y}", f"{y}-{mo:02d}"]
    if re.fullmatch(r"\d{4}", lab):
        return [lab]
    if re.fullmatch(r"(?i)(ceh|nw|wmc|lis|fe|d|t)\d+[a-z]?", lab):
        return [lab.lower()]
    if re.fullmatch(r"(?i)c[1-5]", lab):
        return CLUSTER_NAMES[lab.lower()]
    words = [w.lower() for w in re.split(r"[^A-Za-z0-9²]+", lab) if len(w) >= 2 and not w.isdigit()]
    if any(re.fullmatch(r"(?i)c[1-5]", w) for w in words):
        words = words + [x for w in words if re.fullmatch(r"(?i)c[1-5]", w) for x in CLUSTER_NAMES[w.lower()]]
    out = []
    for w in words:
        if w in LABEL_SYNONYMS:
            out.extend(LABEL_SYNONYMS[w])
        elif len(w) >= 3 and w not in _DEEP_STOP:
            out.append(w)
    return out


def _col_anchors(c: str) -> list[str]:
    words = [w.lower() for w in re.split(r"[^A-Za-z0-9²]+", str(c)) if w]
    out = []
    for w in words:
        if w in COLUMN_SYNONYMS:
            out.extend(COLUMN_SYNONYMS[w])
        elif len(w) >= 3 and w not in _COL_STOP:
            out.append(w)
    return out


def _add(look, key, cand):
    look[key].append(cand)


def _renderings(x: float):
    """(rendering, form) pairs for a value: plain at 0–6 dp, mm, %."""
    import math
    x = float(x)                      # numpy scalars: repr() would be np.float64(...)
    if not math.isfinite(x):
        return
    for dp in range(0, 7):
        yield cc.render(abs(x), dp), ""
    mm = abs(x) * 1000.0
    import decimal as _d
    for dp in (0, 1, 2):
        yield cc.render(mm, dp), "mm"
        yield str(_d.Decimal(repr(mm)).quantize(_d.Decimal(1).scaleb(-dp), rounding=_d.ROUND_HALF_UP)), "mm"
    if 0 < abs(x) <= 1:
        for dp in (0, 1):
            yield cc.render(abs(x) * 100, dp), "%"


_LAKE = re.compile(r"(?i)llyn|lake|rhos")
_WELL_FILES = ("outputs/01_wells_reference.csv", "outputs/01_wells_extended.csv",
               "outputs/01_wells_clean.csv", "outputs/01_wells_all.csv")
_NET_ANC = {"col": ["wells", "dipwells", "well", "network", "boreholes", "points", "sites"],
            "file": [], "stat": ["wells", "dipwells", "network", "measuring", "points", "reference",
                                 "extended", "boreholes", "sites", "across", "covers", "comprises"]}


def _well_columns(rel: str) -> tuple[list[str], list[str]]:
    """(well columns, lake columns) of a wide 01_wells_* matrix."""
    f = REPO / rel
    if not f.exists():
        return [], []
    with open(f, encoding="utf8", newline="") as fh:
        head = next(csv.reader(fh))
    wells = [c for c in head[1:] if not _LAKE.search(c)]
    lakes = [c for c in head[1:] if _LAKE.search(c)]
    return wells, lakes


def _network_counts(look) -> None:
    """Well counts are COUNTS OF COLUMNS, not cells (Martin, 2026-09-20: "88 should
    relate to the well count minus the lake"). 66 reference + 22 extended = 88
    dipwells; the lake gauge is a measuring point, not a well, so wells_clean's
    column set less its lake column is another count, and plus it is the
    "measuring points" figure. Every derived count names its arithmetic."""
    counts = {}
    for rel in _WELL_FILES:
        wells, lakes = _well_columns(rel)
        if not wells:
            continue
        stem = pathlib.Path(rel).stem.replace("01_wells_", "")
        counts[stem] = (rel, len(wells), len(lakes))
        _add_net(look, rel, f"{len(wells)} well columns in {stem} (lake excluded)", len(wells))
        if lakes:
            _add_net(look, rel, f"{len(wells)} wells + {len(lakes)} lake column in {stem} = measuring points", len(wells) + len(lakes))
    if "reference" in counts and "extended" in counts:
        r, e = counts["reference"], counts["extended"]
        _add_net(look, "outputs/01_wells_reference.csv",
                 f"{r[1]} reference + {e[1]} extended well columns = {r[1] + e[1]} dipwells", r[1] + e[1])
        _add_net(look, "outputs/01_wells_reference.csv",
                 f"{r[1]} reference + {e[1]} extended + 1 lake gauge = {r[1] + e[1] + 1} measuring points", r[1] + e[1] + 1)


def _add_net(look, rel, label, n) -> None:
    for r, form in _renderings(float(n)):
        if form == "":
            _add(look, r, Cand(rel, label, "", float(n), _NET_ANC, form, "net"))


def _cluster_count(look) -> None:
    """k is the number of distinct clusters in Script 02's membership CSV (Martin,
    2026-09-20: "k = 5 should be relating to the clustering script 02 csvs")."""
    import pandas as pd
    anc = {"col": ["k", "clusters", "cluster", "partition", "clustering", "solution"], "file": [],
           "stat": ["k", "clusters", "partition", "solution", "clustering", "identified", "five", "into"]}
    for rel, col in (("outputs/02_clustering/02_07_cluster_membership_k5.csv", "cluster_k5"),
                     ("outputs/02_cluster_stats.csv", "Cluster")):
        f = REPO / rel
        if not f.exists():
            continue
        try:
            k = int(pd.read_csv(f)[col].nunique())
        except Exception:
            continue
        for r, form in _renderings(float(k)):
            if form == "":
                _add(look, r, Cand(rel, f"distinct clusters in {col} (k = {k})", col, float(k), anc, form, "net"))


KML_MAX_POLYGONS = 8              # a boundary file; the DEM-basin and flood-extent KMLs run to thousands


def _kml_areas(look) -> None:
    """Polygon areas of data/geo/*.kml in hectares (Martin, 2026-09-20: "the source
    is the clearfell kml"). Equirectangular at the polygon's mean latitude —
    within 0.1% of the OSGB36 figure at this size — so no geopandas is needed.
    Anchored on the file's and placemark's words and a hectare unit."""
    import math
    geo = REPO / "data" / "geo"
    if not geo.is_dir():
        return
    for p in sorted(geo.glob("*.kml")):
        try:
            txt = p.read_text(encoding="utf8", errors="ignore")
        except OSError:
            continue
        polys = re.findall(r"<Polygon>.*?<coordinates>(.*?)</coordinates>", txt, re.S)
        if not polys or len(polys) > KML_MAX_POLYGONS:
            continue                          # a basin or flood-extent file, not a boundary anyone quotes
        names = [n.strip() for n in re.findall(r"<name>(.*?)</name>", txt, re.S)]
        words = sorted({w for n in [p.stem] + names for w in _deep_words(n.replace("_", " ").replace("-", " "))} - WEAK_ANCHORS)
        if not words:
            continue
        areas = []
        for coords in polys:
            pts = []
            for tok in coords.split():
                try:
                    x, y = (float(v) for v in tok.split(",")[:2])
                except ValueError:
                    continue
                pts.append((x, y))
            if len(pts) < 3:
                continue
            lat0 = sum(q[1] for q in pts) / len(pts)
            R = 6371000.0
            xy = [(math.radians(x) * R * math.cos(math.radians(lat0)), math.radians(y) * R) for x, y in pts]
            a = 0.0
            for i in range(len(xy)):
                x1, y1 = xy[i]
                x2, y2 = xy[(i + 1) % len(xy)]
                a += x1 * y2 - x2 * y1
            areas.append(abs(a) / 2 / 1e4)
        if not areas:
            continue
        rel = str(p.relative_to(REPO))
        anc = {"col": words, "file": [], "stat": ["ha", "hectare", "hectares", "area"]}
        vals = [("polygon area", sum(areas))] + ([(f"polygon {i + 1} area", a) for i, a in enumerate(areas)] if len(areas) > 1 else [])
        for lab, v in vals:
            for r, form in _renderings(v):
                if form == "":
                    _add(look, r, Cand(rel, f"{p.name} {lab} = {v:.2f} ha", "area_ha", v, anc, form, "geo"))


def build_index(values, deep: bool = True) -> dict:
    import pandas as pd
    look: dict[str, list] = defaultdict(list)
    global REG_FILES
    REG_FILES = {src for src, _, _ in values}
    # cite_check 1.19.0 admits mixed-case constants (SD15b); this stays as a
    # belt-and-braces scan for an older cite_check on another machine.
    known = {(src, lab) for src, lab, _ in values}
    extra = re.compile(r"(?m)^([A-Z][A-Za-z0-9_]{2,})\s*=\s*(-?\d+(?:\.\d+)?)\s*(?:#|$)")
    for rel in cc.CONSTANT_SOURCES:
        f = REPO / rel
        if f.exists():
            for m in extra.finditer(f.read_text(encoding="utf8")):
                if (rel, m.group(1)) not in known:
                    values = list(values) + [(rel, m.group(1), float(m.group(2)))]
    for src, lab, v in values:                       # the registered tier
        for r, form in _renderings(v):
            _add(look, r, Cand(src, lab, "", v, None, form, "reg"))
    # DERIVED from the thresholds: "spans only 37 cm" is SD16 − SD15b (Martin: "it's
    # the difference in the current thresholds; you should be able to read the
    # context and derive these numbers"). Every pairwise difference of the SD
    # constants, labelled by both names so the tooltip says what was subtracted.
    sds = [(lab, v) for src, lab, v in values if src.endswith("config.py") and lab.upper().startswith("SD1")]
    for i, (la, va) in enumerate(sds):
        for lb, vb in sds[i + 1:]:
            dv = abs(va - vb)
            if dv <= 0:
                continue
            anc = {"col": [la.lower(), lb.lower(), "threshold", "thresholds", "spans", "gradient", "between"], "file": [], "stat": ["spans", "between", "from", "to", "difference", "gradient", "only", "wide"]}
            for r, form in _renderings(dv):
                _add(look, r, Cand("src/utils/config.py", f"{la} − {lb} = {dv:g} m", "", dv, anc, form, "stat"))
            for r, form in (("%d" % round(dv * 100), ""), ("%.0f" % (dv * 100), "")):
                _add(look, r, Cand("src/utils/config.py", f"{la} − {lb} = {dv * 100:g} cm", "", dv * 100, anc, "", "stat"))
    _network_counts(look)
    _cluster_count(look)
    _kml_areas(look)
    if not deep:
        return look
    for root in DEEP_ROOTS:
        for p in sorted((REPO / root).rglob("*.csv")):
            rel = str(p.relative_to(REPO))
            if p.stat().st_size > DEEP_MAX_BYTES or cc._excluded(rel):
                continue
            try:
                df = pd.read_csv(p)
            except Exception:
                continue
            if len(df) > DEEP_MAX_ROWS or df.shape[1] < 2:
                continue
            fw = _deep_words(p.stem.replace("_", " "))
            kcol = df.columns[0]
            dated = pd.to_datetime(df[kcol], errors="coerce")
            monthly = dated.notna().mean() > 0.9 and len(df) >= 24
            for c in df.columns[1:]:
                col = pd.to_numeric(df[c], errors="coerce")
                cw = _col_anchors(c)
                good = col.dropna()
                if len(good) >= 3 and cw:
                    colw = _col_anchors(c)
                    for stat, val in (("min", float(good.min())), ("max", float(good.max())),
                                      ("median", float(good.median())), ("mean", float(good.mean()))):
                        anc = {"col": colw, "file": fw, "stat": STAT_WORDS[stat]}
                        for r, form in _renderings(val):
                            _add(look, r, Cand(rel, f"{stat} of {c}", c, val, anc, form, "stat"))
                    if monthly:
                        roll = col.rolling(12).mean().dropna()
                        if len(roll):
                            for stat, val in (("min", float(roll.min())), ("max", float(roll.max()))):
                                anc = {"col": colw, "file": fw, "stat": STAT_WORDS[stat], "roll": ROLL_WORDS}
                                for r, form in _renderings(val):
                                    _add(look, r, Cand(rel, f"rolling-12 {stat} of {c}", c, val, anc, form, "roll"))
            notecol = next((c for c in df.columns if c.lower() in ("note", "notes", "description")), None)
            # A PER-WELL TABLE WITH A CLUSTER COLUMN: the prose quotes cluster-level
            # statistics of it — "C4 mean 1.65×, range 1.36–2.20×" of
            # 35_per_well_amplification's amp_coefficient. Per cluster, per numeric
            # column: mean, median, min, max, anchored on the cluster's names and
            # the column's words.
            ccol = next((c for c in df.columns if c.lower() in ("cluster", "cluster_id", "cluster_label")), None)
            if ccol is not None and len(df) >= 10:
                try:
                    groups = df.groupby(ccol)
                except Exception:
                    groups = None
                if groups is not None:
                    for gkey, g in groups:
                        m = re.search(r"[1-5]", str(gkey))
                        if not m or not (str(gkey).strip().lower().startswith("c") or str(gkey).strip().replace(".0", "").isdigit()):
                            continue
                        cname = "c" + m.group()
                        for c in df.columns[1:]:
                            if c == ccol:
                                continue
                            col = pd.to_numeric(g[c], errors="coerce").dropna()
                            colw = _col_anchors(c)
                            if len(col) < 3 or not colw:
                                continue
                            for stat, val in (("mean", float(col.mean())), ("median", float(col.median())),
                                              ("min", float(col.min())), ("max", float(col.max()))):
                                anc = {"col": colw, "file": fw, "stat": STAT_WORDS[stat], "label": CLUSTER_NAMES[cname]}
                                for r, form in _renderings(val):
                                    _add(look, r, Cand(rel, f"{cname.upper()} {stat} of {c}", c, val, anc, form, "gstat"))
            # A WIDE MONTHLY MATRIX (wells as columns): the sentence quotes statistics
            # of statistics — "individual well means ranging from 0.26 m to 2.07 m",
            # "the network mean across all wells and months was 0.77 m" (Martin,
            # 2026-09-20, on 01_wells_reference.csv). Per-column means, minima,
            # maxima and medians, then their min/max/median/mean across columns,
            # plus the grand mean over every cell.
            numcols = [c for c in df.columns[1:] if pd.to_numeric(df[c], errors="coerce").notna().sum() >= 12]
            if monthly and len(numcols) >= 10:
                wide = df[numcols].apply(pd.to_numeric, errors="coerce")
                INNER = {"mean": ["mean", "means", "average"], "min": ["minimum", "minima", "lowest", "deepest"],
                         "max": ["maximum", "maxima", "shallowest", "highest"], "median": ["median", "medians"]}
                per = {"mean": wide.mean(), "min": wide.min(), "max": wide.max(), "median": wide.median()}
                colw = ["well", "wells", "individual", "network", "site", "per-well"]
                for inner, series in per.items():
                    series = series.dropna()
                    for outer, val in (("min", float(series.min())), ("max", float(series.max())),
                                       ("median", float(series.median())), ("mean", float(series.mean()))):
                        anc = {"col": colw + INNER[inner], "file": fw, "stat": STAT_WORDS[outer]}
                        for r, form in _renderings(val):
                            _add(look, r, Cand(rel, f"{outer} of per-column {inner}s", "", val, anc, form, "stat"))
                grand = float(wide.stack().mean())
                for r, form in _renderings(grand):
                    _add(look, r, Cand(rel, "mean over all columns and rows", "", grand,
                                       {"col": colw, "file": fw, "stat": ["mean", "average", "across all"]}, form, "stat"))
            for _, r_ in df.iterrows():
                lab = str(r_[kcol])
                la = _label_anchors(lab)
                if ccol is not None:                  # "clearfell · C4": the row's cluster is part of its name
                    cl = str(r_[ccol]).strip()
                    mcl = re.search(r"[1-5]", cl)
                    if mcl and (cl.lower().startswith("c") or cl.replace(".0", "").isdigit()):
                        lab = f"{lab} · C{mcl.group()}"
                        la = la + CLUSTER_NAMES["c" + mcl.group()]
                notew = [w for w in _deep_words(r_[notecol]) if len(w) >= 5 and w not in WEAK_ANCHORS][:12] \
                    if notecol is not None and isinstance(r_[notecol], str) else []
                rowvals = {}
                for c in df.columns[1:]:
                    try:
                        x = float(r_[c])
                    except (TypeError, ValueError):
                        continue
                    if x != x:
                        continue
                    rowvals[c] = x
                    anc = {"label": la, "col": _col_anchors(c) + notew, "file": fw}
                    for r, form in _renderings(x):
                        _add(look, r, Cand(rel, lab, c, x, anc, form, "cell"))
                if rowvals:
                    ROWS[(rel, lab)] = rowvals
    return look


# ---------------------------------------------------------------------------
# what each section's sources are
# ---------------------------------------------------------------------------
_SRC_RE = re.compile(r"\(Source:?\s*([^)]+)\)")
_SCRIPT_RE = re.compile(r"\bScript\s+(\d{2}[a-z]?)\b")
_EXHIBIT_RE = re.compile(r"\b(Figure|Table)\s+(\d+(?:\.\d+)?)")
_OUTPUT_FILES: dict | None = None


def _output_index() -> dict:
    global _OUTPUT_FILES
    if _OUTPUT_FILES is None:
        idx = defaultdict(list)
        for root in DEEP_ROOTS:
            for p in (REPO / root).rglob("*"):
                if p.is_file():
                    idx[p.name].append(str(p.parent.relative_to(REPO)))
        _OUTPUT_FILES = idx
    return _OUTPUT_FILES


def _scope_for_name(name: str) -> set[str]:
    """A file name -> its directory (so the script's whole output set is in scope)."""
    name = name.strip().split()[0] if name.strip() else ""
    return set(_output_index().get(name, []))


def _scope_for_script(num: str) -> set[str]:
    base = re.match(r"\d{2}", num).group()
    out = set()
    for p in (REPO / "outputs").glob(f"{base}*"):
        if p.is_dir() and (p.name.startswith(base + "_") or re.match(base + r"[a-z]_", p.name)):
            out.add(str(p.relative_to(REPO)))
        elif p.is_file() and p.suffix == ".csv":
            out.add(str(p.relative_to(REPO)))          # 01_climate.csv sits at outputs/ root
    return out


def _scope_token(pattern: str) -> set[str]:
    """A proof_scope.csv entry -> scope tokens (dirs, or file paths for globs)."""
    pattern = pattern.strip()
    if not pattern:
        return set()
    hits = {str(p.relative_to(REPO)) for p in REPO.glob(pattern)}
    if not hits and (REPO / pattern).exists():
        hits = {pattern}
    return hits


def load_scope_file(doc_stem: str) -> list[tuple[str, set[str]]]:
    rows = []
    if SCOPE_FILE.exists():
        with open(SCOPE_FILE, encoding="utf8") as fh:
            for r in csv.DictReader(fh):
                if r["document"].strip() == doc_stem:
                    toks = set()
                    for part in r["sources"].split(";"):
                        toks |= _scope_token(part)
                    rows.append((r["section"].strip(), toks))
    return rows


def section_scope(text: str, secs, doc_stem: str) -> dict:
    """{(num, heading): (scope tokens, how)} — how is 'file', 'declared' or ''."""
    manifest = {}
    if MANIFEST.exists():
        with open(MANIFEST, encoding="utf8") as fh:
            for r in csv.DictReader(fh):
                if pathlib.Path(r["document"]).stem == doc_stem:
                    manifest[(r["type"], r["number"])] = r["source_file"]
    lines = text.split("\n")
    bounds = [(ln, (num, h)) for ln, num, h in secs] + [(len(lines), None)]
    declared = {}
    for (a, key), (b, _) in zip(bounds, bounds[1:]):
        if key is None:
            continue
        body = "\n".join(lines[a:b])
        toks = set()
        for m in _SRC_RE.finditer(body):
            for part in re.split(r"[;,]\s*", m.group(1)):
                toks |= _scope_for_name(part)
        for m in _SCRIPT_RE.finditer(body):
            toks |= _scope_for_script(m.group(1))
        for m in _EXHIBIT_RE.finditer(body):
            src = manifest.get((m.group(1), m.group(2)))
            if src:
                toks |= _scope_for_name(src)
        declared[key] = toks
    # inherit the parent's declarations
    bynum = {k[0]: k for k in declared}
    for k in list(declared):
        num = k[0]
        while "." in num:
            num = num.rsplit(".", 1)[0]
            if num in bynum:
                declared[k] = declared[k] | declared[bynum[num]]
    file_rows = load_scope_file(doc_stem)
    out = {}
    for k in declared:
        best = None
        for prefix, toks in file_rows:            # the longest matching prefix wins
            if k[0] == prefix or k[0].startswith(prefix + "."):
                if best is None or len(prefix) > len(best[0]):
                    best = (prefix, toks)
        if best:
            out[k] = (best[1], "file")
        elif declared[k]:
            out[k] = (declared[k], "declared")
        else:
            out[k] = (set(), "")
    return out


_PARENT: dict[str, str] = {}


ALWAYS_IN_SCOPE = set(cc.CONSTANT_SOURCES) | {"outputs/pipeline_manifest.json"}


def in_scope(c: Cand, scope: set[str]) -> bool:
    """config.py's constants and the manifest counts are cited from every section;
    a threshold like SD16 = 0.98 is in scope everywhere."""
    rel = c.rel
    if rel in ALWAYS_IN_SCOPE or c.tier in ("net", "geo"):
        return True                      # network counts and site geometry are cited everywhere
    d = _PARENT.get(rel)
    if d is None:
        d = _PARENT[rel] = str(pathlib.Path(rel).parent)
    return rel in scope or d in scope


# ---------------------------------------------------------------------------
# classification
# ---------------------------------------------------------------------------
_NUM = re.compile(r"(?:(?<![\w.\-−–—])[+\-−–]?|(?<=[\-−–—]))"
                  r"\d+(?:[.,]\d+)*(?![\w])")
_YEAR = re.compile(r"^(?:18|19|20)\d\d$")
_GLUE_BEFORE = re.compile(r"[A-Za-z][\-‑]$")
_GLUE_AFTER = re.compile(r"[\-‑][A-Za-z]")
_LIST_MARKER = re.compile(r"^\d+\.\s")
_IDENT_CHAIN = re.compile(r"\d+[-‐]\d+[-‐]\d+")          # three digit groups joined by hyphens
_PCT_AFTER = re.compile(r"(?i)^\s*(?:%|per cent|percent)")
_HA_AFTER = re.compile(r"(?i)^\s*(?:ha|hectares?)\b")
_NOMINAL_AFTER = re.compile(r"(?i)^\s*%?\s*(?:thinning|thinned|canopy removal|felling scenario)")   # "50% thinning" names a scenario
_AREA_KEY = re.compile(r"(?i)area|_ha\b|hectare")
_RANGE_AFTER = re.compile(r"^\s*(?:--|[\-\u2013\u2014]|to|and)\s*[+\-\u2212]?\d+(?:[.,]\d+)*")
_BOUND_BEFORE = re.compile(r"(p|n|r²|R²)?\s*\\?([<>≤≥])\s*$")
_PCOL = re.compile(r"(?i)^(p|p_?val(ue)?|pvalue|p_value_.*|.*_p)$")
# "p = 0.25" is a probability, not a slope (Martin, 2026-09-20): the letter before
# "=" names the quantity, and only a candidate whose column or key is that quantity
# may be cited for it. Applied to p, r, R², n, k.
_QTY_BEFORE = re.compile(r"(?i)(?<![a-z0-9²_])(p|r²|r2|r|n|k)\s*=\s*$")   # not m_P = 2.5
_QTY_PAT = {
    "p": re.compile(r"(?i)(^|_)(p|pval|pvalue|p_value|p_val|prob|significance)(_|$)|_p$|^p_"),
    "r": re.compile(r"(?i)(^|_)(r|rho|pearson|spearman|corr|correlation|affinity)(_|$)"),
    "r²": re.compile(r"(?i)(^|_)(r2|rsq|r_squared|rsquared|r²|adj_r2|r2_adj)(_|$)|r2|r_squared"),
    "n": re.compile(r"(?i)(^|_)(n|n_wells|n_obs|n_months|n_years|count|total|nobs|wells|columns|events)(_|$)|^n_|_n$|\bwell columns\b|dipwells|measuring points"),
    "k": re.compile(r"(?i)(^|_)(k|n_clusters|clusters)(_|$)|distinct clusters|clusters in"),
}


def _qty_of(masked: str, s: int) -> str | None:
    m = _QTY_BEFORE.search(masked[max(0, s - 8):s])
    if not m:
        return None
    q = m.group(1).lower()
    return "r²" if q in ("r2", "r²") else q


def _qty_ok(q: str, c: Cand) -> bool:
    pat = _QTY_PAT[q]
    return bool(pat.search(c.col or "") or pat.search(c.label or ""))
COHERENCE_WINDOW = 260          # characters: a sentence and its neighbour


def mask_markup(text: str) -> str:
    f = lambda m: " " * len(m.group())
    return cc._IMGREF.sub(f, cc._MARKUP.sub(f, text)).replace("*", " ")


_WORD = re.compile(r"[a-z0-9²½₀₁₂₃βδλκτ]+")


def _hit(a: str, w: str, ws: set) -> bool:
    """An anchor is present: whole-word for short anchors ("rec" must not match
    "record"), substring for longer ones (so "amplif" catches "amplification")."""
    a = a.lower()
    if len(a) <= 4 and " " not in a:
        return a in ws
    return a in w


_NONLEN = re.compile(r"(?i)pct|percent|ratio|fraction|_p$|pvalue|r2|rsq|count|_n$|index|years?|months?|days?")
_CLUSTER_ID = re.compile(r"(?i)(?<![a-z0-9])c([1-5])(?![0-9])")
_CLUSTER_WORDS = {"lake edge": "1", "western residual": "3", "main forest": "4", "coastal forest": "5"}   # "dune" alone is a landform


_CL_CACHE: dict[str, frozenset] = {}
_CAND_CL: dict[tuple, frozenset] = {}


def _clusters_in(text: str) -> frozenset:
    hit = _CL_CACHE.get(text)
    if hit is None:
        if len(_CL_CACHE) > 20000:
            _CL_CACHE.clear()
        out = {m.group(1) for m in _CLUSTER_ID.finditer(text)}
        low = text.lower()
        out |= {k for w, k in _CLUSTER_WORDS.items() if w in low}
        hit = _CL_CACHE[text] = frozenset(out)
    return hit


_SENT_END = re.compile(r"[.!?;]\s|\n")


def _rowkey(label: str) -> str:
    """A row's name with its cluster removed, so 'thinning / annual / C4' and
    'thinning / annual / C5' count as the SAME row for the coherence pass: a
    sentence that quotes C4 then C5 from one scenario is reading one line of the
    table across."""
    return _CLUSTER_ID.sub("", label).replace("  ", " ").strip(" /·")


_SENT_CACHE: dict[tuple, str] = {}


def _sentence(masked: str, s: int, e: int) -> str:
    hit = _SENT_CACHE.get((s, e))
    if hit is None:
        hit = _SENT_CACHE[(s, e)] = _sentence_uncached(masked, s, e)
    return hit


_SW_CACHE: dict[str, set] = {}


def _sent_words(sent: str) -> set:
    hit = _SW_CACHE.get(sent)
    if hit is None:
        if len(_SW_CACHE) > 4000:
            _SW_CACHE.clear()
        hit = _SW_CACHE[sent] = set(_WORD.findall(sent))
    return hit


def _sentence_uncached(masked: str, s: int, e: int) -> str:
    """The clause the token sits in — from the previous sentence end (or ';' / ':',
    which in this corpus separate the items of a list) to the next. The anchor
    window is a paragraph wide, which is right for finding a key's words but
    wrong for choosing between keys: in the abstract every scenario name sits
    within 300 characters of every scenario number."""
    lo = 0
    for m in _SENT_END.finditer(masked, max(0, s - 400), s):
        lo = m.end()
    m2 = _SENT_END.search(masked, e, e + 400)
    hi = m2.start() if m2 else e + 400
    return masked[lo:hi].lower()


def _cluster_clash(c: Cand, w: str) -> bool:
    """The sentence names C4 and C5; a candidate from a C2 row is not it (Martin,
    2026-09-20: "the C4 reference prior should have caught this"). Only vetoes
    when BOTH the text and the candidate name clusters and they share none."""
    key = (c.label, c.col)
    mine = _CAND_CL.get(key)
    if mine is None:
        mine = _CAND_CL[key] = _clusters_in(c.label + " " + (c.col or ""))
    if not mine:
        return False
    theirs = _clusters_in(w)
    return bool(theirs) and not (mine & theirs)


_LABEL_WORD = re.compile(r"[a-z0-9]+")


_LW_CACHE: dict[str, tuple] = {}


def _label_words(label: str) -> tuple:
    hit = _LW_CACHE.get(label)
    if hit is None:
        hit = _LW_CACHE[label] = tuple(wd for wd in set(_LABEL_WORD.findall(label.lower()))
                                       if wd not in cc._STOPWORDS and len(wd) >= 2)
    return hit


def _label_hits(label: str, w: str, ws: set) -> int:
    n = 0
    for wd in _label_words(label):
        if wd in ws or (len(wd) >= 5 and wd in w):
            n += 1
    return n


def _accept(c: Cand, masked: str, s: int, e: int, short: bool, w: str, ws: set, inside: bool, scoped: bool = False,
            unit: str = "") -> float:
    """Score a candidate at this position; 0 = not a citation. A registered value
    scores 3 when its key anchors here. A CSV cell scores 2 for its row label,
    1 for a column word, 0.5 for a file word; a derived statistic needs its
    column AND its statistic word; a rolling-mean extreme needs the column and
    'rolling'. In scope a short whole number needs 1, outside it needs 2; unit
    conversions (mm, %) lose 0.5 so a plain rendering wins a tie."""
    sent = _sentence(masked, s, e)
    if _cluster_clash(c, sent):
        return 0
    if c.tier == "reg":
        weak = not cc.searchable(cc.render(abs(c.value), _dp_of(masked[s:e].lstrip("+-\u2212\u2013"))), c.label)
        if not anchored_here(masked, s, e, c.label, strict=weak or short, w=w):
            return 0
        # a key whose SUBJECT (cluster, well) and QUANTITY both sit in the window
        # outranks one that merely shares a word; a global constant outranks
        # nothing from the section's own sources
        score = 4 if anchored_here(masked, s, e, c.label, strict=True, w=w) else 3
        if c.rel in ALWAYS_IN_SCOPE and inside and scoped:
            score -= 0.5
        # tie-breaker among registered keys that all anchor: the one MORE of whose
        # own words sit in the sentence. "thinning / annual / C5" (three words
        # present) outranks "ukcp18_2080s / winter / C4" (one) for a 6.1 that both
        # render — which is how the abstract's thinning figure was painted against a
        # climate-scenario winter row (2026-09-20).
        score += 0.1 * min(5, _label_hits(c.label, sent, _sent_words(sent)))
        return score
    a = c.anchors
    score = 0.0
    if c.tier in ("stat", "roll", "gstat", "net", "geo"):
        colhits = sum(1 for x in set(a["col"]) if _hit(x, w, ws))
        stathit = any(x in w for x in a["stat"])
        rollhit = any(x in w for x in a.get("roll", []))
        if c.tier == "roll":
            ok = colhits > 0 and rollhit
        elif c.tier == "gstat":
            ok = colhits > 0 and stathit and any(_hit(x, w, ws) for x in a["label"])
        else:
            ok = colhits > 0 and stathit
        score = (2.0 + min(colhits - 1, 2) * 0.5) if ok else 0.0
        if c.tier == "gstat" and ok:
            score += 1.0                          # cluster + column + statistic all present
        if ok and any(_hit(x, w, ws) for x in a["file"]):
            score += 0.5
    else:
        if any(_hit(x, w, ws) for x in a["label"]):
            score += 2
        if any(_hit(x, w, ws) for x in a["col"]):
            score += 1
        if any(_hit(x, w, ws) for x in a["file"]):
            score += 0.5
    if c.form and c.form != unit:
        score -= 0.5                          # a converted rendering with no unit in the text
    elif unit == "mm" and not c.form and (_NONLEN.search(c.label + " " + (c.col or "")) or re.search(r"_M$|_m$|_M\b", c.label)):
        score -= 1.0                          # "+113 mm" is a length: a percentage, or a constant in METRES, sharing the digits is not it
    need = 1 if inside else 2
    if short:
        need += 0 if inside else 1
        if len(masked[s:e].strip("+-\u2212\u2013")) <= 2:
            need += 1.5                            # "12", "n = 5": label and column both
    return score if score >= need else 0.0


def classify(text: str, look: dict, idx: dict, secs, scope_map: dict):
    _SENT_CACHE.clear()
    masked = mask_markup(text)
    idx_by_start = {k[0]: v for k, v in idx.items()}
    line_starts = [0] + [m.end() for m in re.finditer("\n", text)]

    def sec_of(pos):
        ln = bisect.bisect_right(line_starts, pos) - 1
        cur = None
        for hl, num, h in secs:
            if hl <= ln:
                cur = (num, h)
        return cur

    prelim = []           # (s, e, verdict, detail, options) — options for the coherence pass
    for m in _NUM.finditer(masked):
        s, e = m.start(), m.end()
        tok = m.group()
        if not cc._is_whole_number(masked, s, e) or not cc._citable_context(masked, s, e):
            continue
        if _GLUE_BEFORE.search(masked[max(0, s - 2):s]) or _GLUE_AFTER.match(masked[e:e + 2]):
            continue
        if _IDENT_CHAIN.search(masked[max(0, s - 12):e + 12]) or re.search(r"(?i)\b(orcid|doi|isbn|issn|tel)\b", masked[max(0, s - 24):s]):
            continue                                   # ORCID 0000-0003-…, DOI 10.1016/…
        bol = masked.rfind("\n", 0, s) + 1
        if masked[bol:s].strip() == "" and _LIST_MARKER.match(masked[s:e + 2]):
            continue
        core = _norm_num(tok).replace(",", "")
        unsigned = core.lstrip("-")
        if _YEAR.match(unsigned):
            continue
        scope, how = scope_map.get(sec_of(s), (set(), ""))
        row = idx_by_start.get(s)
        if row and (row["status"] == "confirmed" or row["verdict"] in ("traced", "rounding")):
            # A PROPOSED index row is a machine guess and mispoints inside tables
            # (CLAUDE.md §5): "3.57" in §4.2.2 was pointed at Script 25's δ₀ standard
            # error while the sentence quotes C3's β₁. A proposed row outside the
            # section's scope is ignored; a confirmed row is believed but noted.
            src = row["source_csv"]
            row_in = (not scope) or src in ALWAYS_IN_SCOPE or src in scope or str(pathlib.Path(src).parent) in scope
            if row["status"] != "confirmed" and _cluster_clash(Cand(src, row["key"], "", 0.0, None, "", "reg"), _sentence(masked, s, e)):
                row = None                                 # a C3 key for a sentence about C4: not believed
            if row is not None and (row["status"] == "confirmed" or row_in):
                det = (f"{row['key']} · {pathlib.Path(src).name} · "
                       f"committed {row['committed']!r} · index {row['status']}"
                       + ("" if row_in else " — NB outside this section's sources"))
                prelim.append((s, e, row["verdict"], det, []))
                continue
        if _NOMINAL_AFTER.match(masked[e:e + 24]):
            prelim.append((s, e, "count", "nominal scenario parameter (Martin: 'it doesn't trace')", []))
            continue
        bm = _BOUND_BEFORE.search(masked[max(0, s - 6):s])
        if bm:
            prelim.append((s, e, "bound", f"{(bm.group(1) or '').strip()} {bm.group(2)} {unsigned}", []))
            continue
        after = masked[e:e + 16]
        after = _RANGE_AFTER.sub("", after)                # "50--55 mm": look past the range
        pct = bool(_PCT_AFTER.match(after))
        mm = bool(cc._MM_SUFFIX.match(after))
        unit = "mm" if mm else "%" if pct else ""
        short = "." not in unsigned and len(unsigned) <= 3
        w = masked[max(0, s - cc.ANCHOR_WINDOW): e + cc.ANCHOR_WINDOW].lower()
        ws = set(_WORD.findall(w))
        cands = [c for c in look.get(unsigned, [])
                 if (c.form == "") or (c.form == "%" and pct) or (c.form == "mm" and mm)]
        qty = _qty_of(masked, s)
        if qty:
            cands = [c for c in cands if _qty_ok(qty, c)]
        if _HA_AFTER.match(after):                         # "8.4 ha" is an area: geometry or an area key only
            cands = [c for c in cands if c.tier == "geo" or _AREA_KEY.search((c.col or "") + " " + c.label)]
        inside, outside = [], []
        of_prev = None
        if re.search(r"\bof\s*$", masked[max(0, s - 4):s]) and prelim and prelim[-1][2] == "in" and abs(prelim[-1][1] - s) <= 12:
            of_prev = prelim[-1][4][0][1].rel if prelim[-1][4] else None
        for c in cands:
            if not scope or in_scope(c, scope):
                sc = _accept(c, masked, s, e, short, w, ws, True, bool(scope), unit)
                if sc == 0 and of_prev and c.rel == of_prev and re.search(r"(?i)(^|_)(n|n_wells|total|count)(_|$)|n_wells|_n$", c.label):
                    sc = 2                             # the N of "n of N", from the n's file
                if sc > 0:
                    inside.append((sc, c))
        if not inside and len(cands) <= 4000:
            for c in cands:
                if scope and not in_scope(c, scope):
                    sc = _accept(c, masked, s, e, short, w, ws, False, unit=unit)
                    if sc > 0:
                        outside.append((sc, c))
        if inside:
            inside.sort(key=lambda t: (-t[0], t[1].tier != "reg"))
            prelim.append((s, e, "in", qty or "", inside))
            continue
        if qty and not outside:
            prelim.append((s, e, "qty", f"{qty} {unsigned}", []))
            continue                                   # resolved against the neighbours' row below
        if outside:
            outside.sort(key=lambda t: (-t[0], t[1].tier != "reg"))
            sc, c = outside[0]
            cites = ", ".join(sorted(pathlib.Path(x).name for x in scope)[:4])
            prelim.append((s, e, "elsewhere",
                           f"{pathlib.Path(c.rel).name} · {c.label} · {c.col} = {c.value:g} — but this "
                           f"section's sources ({'proof_scope.csv' if how == 'file' else 'declared'}: {cites}) "
                           f"do not carry this number: stale, or the source is undeclared", []))
            continue
        # rounding: one unit off a registered value, in scope
        dp = _dp_of(unsigned)
        try:
            x = float(unsigned)
        except ValueError:
            continue
        near = None
        if cc.searchable(unsigned):
            for k in (-1, 1):
                for c in look.get(cc.render(x + k * 10 ** -dp, dp), []):
                    if c.tier == "reg" and c.form == "" and (not scope or in_scope(c, scope)) \
                            and anchored_here(masked, s, e, c.label, strict=True):
                        near = c
        if near:
            prelim.append((s, e, "rounding", f"one unit off {near.label} = {near.value:g} "
                                             f"[{pathlib.Path(near.rel).name}]", []))
            continue
        if short:
            prelim.append((s, e, "count", "whole number; no committed value to check against", []))
            continue
        cites = ", ".join(sorted(pathlib.Path(x).name for x in scope)[:4]) if scope else "everything"
        prelim.append((s, e, "untraced", f"not in this section's sources ({cites}) at any precision, "
                                         f"and anchored nowhere else", []))

    # --- coherence pass: a sentence's numbers come from one row --------------
    chosen_rows = []                     # (pos, rel, label)
    marks = []
    for s, e, v, d, options in prelim:
        if v == "in":
            near_rows = [(rel, _rowkey(lab)) for pos, rel, lab in chosen_rows if abs(pos - s) <= COHERENCE_WINDOW]
            # "65 of 66 wells": the N belongs to the file the n came from (Martin:
            # "you should be referring to the previous number source when talking
            # about n out of N"), so a same-file candidate that reads as a total
            # outranks everything else for the number after "of"
            of_n = bool(re.search(r"\bof\s*$", masked[max(0, s - 4):s])) and chosen_rows and abs(chosen_rows[-1][0] - s) <= 12
            prev_rel = chosen_rows[-1][1] if of_n else None
            def key(t):
                sc, c = t
                same = (c.rel, _rowkey(c.label)) in near_rows
                samefile = any(r == c.rel for r, _ in near_rows)
                bonus = (1.5 if same else 0.5 if samefile else 0) if sc >= 2 else 0
                if of_n and c.rel == prev_rel and re.search(r"(?i)(^|_)(n|n_wells|total|count)(_|$)|n_wells|_n$", c.label):
                    bonus += 3
                if d and c.tier == "net":
                    bonus += 2                       # "k = 5": Script 02's partition, not the constant that asked for it
                return (-(sc + bonus), c.tier != "reg")
            options.sort(key=key)
            sc, c = options[0]
            chosen_rows.append((s, c.rel, c.label))
            verdict = "traced" if (c.tier == "reg" or c.rel in REG_FILES) else "deep"
            same = (c.rel, _rowkey(c.label)) in near_rows
            det = (f"{c.label}{(' · ' + c.col) if c.col else ''} = {c.value:g} [{pathlib.Path(c.rel).name}]"
                   + (f" as {c.form}" if c.form else "")
                   + (" — same row as its neighbours" if same else "")
                   + ("" if verdict == "traced" else
                      " — DERIVED from the file's geometry/columns; no script emits it (emit list)" if c.tier in ("net", "geo") else
                      " — UNREGISTERED: in no value table; register this file"))
            if len(options) > 1 and (options[1][1].rel, options[1][1].label) != (c.rel, c.label):
                det += f"; also matches {options[1][1].label} [{pathlib.Path(options[1][1].rel).name}]"
            marks.append((s, e, verdict, det))
        else:
            marks.append((s, e, v, d))
    # --- bounds: "p < 0.001" against the p-value of the row its neighbours came from;
    # --- and "p = 0.25" with no p-like candidate of its own: the same row's p
    out = []
    for s, e, v, d in marks:
        if v not in ("bound", "qty"):
            out.append((s, e, v, d)); continue
        if v == "qty":
            what, bound = d.split(" ", 1)
            op = "="
        else:
            what, op, bound = d.split(" ", 2)
        try:
            b = float(bound)
        except ValueError:
            out.append((s, e, "count", "inequality bound")); continue
        near = [(rel, lab) for pos, rel, lab in chosen_rows if abs(pos - s) <= 150]   # the same sentence
        found = None
        if what == "p":
            for rel, lab in near:
                for col, val in ROWS.get((rel, lab), {}).items():
                    if _PCOL.match(col):
                        found = (rel, lab, col, val); break
                if found:
                    break
            if not found:                        # stacked files: p_value is a ROW
                for rel, nlab in near:
                    prows = [(l2, vals) for (r2, l2), vals in ROWS.items()
                             if r2 == rel and _PCOL.match(l2) and vals]
                    if not prows:
                        continue
                    # the p row must belong to the neighbour: same stem
                    # (ANCOVA_Forest_Impact_clearfell_step -> ..._clearfell_p), or the
                    # file is a small block with one p row (00_03: slope / r_squared / p_value)
                    def stem(x):
                        return re.sub(r"_(p|pvalue|p_value|step|slope|coeff|r2|rsq|se|ci_lo|ci_hi|t)$", "", x.lower())
                    same = [(l2, vals) for l2, vals in prows if stem(l2) == stem(nlab) and len(stem(nlab)) >= 4]
                    nrows = sum(1 for (r2, _l) in ROWS if r2 == rel)
                    if not same and len(prows) == 1 and nrows <= 12:
                        same = prows                 # a small stats block: one p, one slope, one R²
                    if same:
                        l2, vals = same[0]
                        col, val = next(iter(vals.items()))
                        found = (rel, l2, col, val); break
        if not found:
            if op == "=":
                out.append((s, e, "untraced", f"quoted as {what} = {bound}: no {what}-like column or key in scope carries it, "
                                               f"and no neighbouring row supplies a {what} to check it against"))
            else:
                out.append((s, e, "count", f"inequality bound ({what} {op} {bound}); no neighbouring row carries a p-value to check it against"))
            continue
        rel, lab, col, val = found
        if op == "=":
            dp = _dp_of(bound)
            holds = cc.render(val, dp) == bound or abs(val - b) < 0.5 * 10 ** -dp
            # a disagreement is not proof of staleness: the sentence's other numbers may
            # come from a row whose p is not this p (a curvature term's p beside a step's
            # row), so it is UNTRACED with the neighbour's p named, not STALE
            out.append((s, e, "traced" if holds else "untraced",
                        f"{what} = {bound}: the row its neighbours cite ({pathlib.Path(rel).name} · {lab}) has "
                        f"{col} = {val:.3g}, which {'agrees at this precision' if holds else 'does not agree — either the p is stale or its quantity is unregistered'}"))
            continue
        holds = (val < b) if op in "<≤" else (val > b)
        out.append((s, e, "traced" if holds else "stale",
                    f"{what} {op} {bound}: the row its neighbours cite ({pathlib.Path(rel).name} · {lab}) has "
                    f"{col} = {val:.3g}, which {'satisfies' if holds else 'CONTRADICTS'} the bound"))
    return out


def index_spans(text: str, rel: str, values):
    """{(start,end): row} for every non-rejected index row located in `text`."""
    byval = {(s, l): v for s, l, v in values}
    out = {}
    with open(cc.CITATION_INDEX, encoding="utf8") as fh:
        for row in csv.DictReader(fh):
            if row["document"] != rel or row["status"] == "rejected":
                continue
            if (row["key"].strip(), rel, row["quoted"].strip()) in cc._FALSE_POSITIVES:
                continue                    # adjudicated by hand: not a citation
            sp = cc.locate(text, row["quoted"], row.get("before", ""), row.get("after", ""))
            if sp is None:
                continue
            v = byval.get((row["source_csv"], row["key"]))
            q = _norm_num(row["quoted"])
            verdict = "unknown"
            if v is not None:
                dp = _dp_of(q)
                if cc.render(v, dp) == q or cc.render(abs(v), dp) == q.lstrip("-"):
                    verdict = "traced"
                else:
                    diff = abs(abs(v) - abs(float(q))) / (10 ** -dp)
                    verdict = "rounding" if diff <= 1.0001 else "stale"
            out[sp] = dict(row, committed=v, verdict=verdict)
    return out


def add_corpus_echo(marks, own_rel: str):
    """For every untraced number, which OTHER documents quote the same rendering.

    Not a check against the pipeline — a check of the corpus against itself,
    which HANDOVER_BOOTSTRAP names as the cheapest habit: nine of the T-15
    findings were internal contradictions. A red number echoed in four other
    documents is at least consistently stated; a red number found nowhere else
    is a singleton, and singletons are where +0.53 lived.
    """
    docs = {d: t for d, t in cc.load_documents().items()
            if d != own_rel and d.split("/")[-1] not in cc.HISTORY_DOCS
            and "VALUE_LEDGER" not in d}
    out = []
    cache: dict[str, str] = {}
    for s, e, v, d in marks:
        if v != "untraced":
            out.append((s, e, v, d)); continue
        tok = _norm_num(TEXT_CACHE[s:e]).lstrip("-")
        if tok not in cache:
            where = [pathlib.Path(doc).stem for doc, t in docs.items() if cc.quotes(t, tok)]
            cache[tok] = (f"also quoted in {', '.join(sorted(where)[:5])}"
                          + (f" (+{len(where) - 5})" if len(where) > 5 else "")
                          if where else "SINGLETON — quoted in no other document")
        out.append((s, e, v, d + "; " + cache[tok]))
    return out


TEXT_CACHE = ""

_HEAD = re.compile(r"^(#{1,4})\s+(.*)$")


def _clean_heading(s: str) -> str:
    s = re.sub(r"\[\]\{#[^}]*\}", "", s)
    s = s.replace("**", "").strip()
    return s


def section_numbers(mirror: pathlib.Path):
    """[(line_no, number, heading)] using tools/section_map.csv by position."""
    heads = []
    for i, line in enumerate(mirror.read_text(encoding="utf8").splitlines()):
        m = _HEAD.match(line)
        if m:
            heads.append((i, len(m.group(1)), _clean_heading(m.group(2))))
    rows = []
    if SECTION_MAP.exists():
        with open(SECTION_MAP, encoding="utf8") as fh:
            rows = [r for r in csv.DictReader(fh)
                    if pathlib.Path(r["document"]).stem == mirror.stem]
    out = []
    for j, (ln, lvl, h) in enumerate(heads):
        num = rows[j]["number"] if j < len(rows) else ""
        out.append((ln, num, h))
    return out


CSS = """
body{font:15px/1.5 Georgia,serif;max-width:60em;margin:1.5em auto;padding:0 1em;color:#222;background:#fff;-webkit-text-size-adjust:100%}
h1,h2,h3,h4{font-family:Helvetica,Arial,sans-serif;line-height:1.25}
h1{font-size:1.5em}h2{font-size:1.25em;margin-top:2em}h3{font-size:1.1em}h4{font-size:1em}
p{margin:.7em 0} pre{font:12px/1.35 Menlo,Consolas,monospace;overflow-x:auto;background:#fafafa;padding:.5em;border:1px solid #eee}
.n{padding:0 .15em;border-radius:3px;cursor:help;border-bottom:2px solid}
.traced{background:#e3f4e3;border-color:#3a3}
.unanchored{background:#eef7ee;border-color:#9c9;border-bottom-style:dotted}
.deep{background:#e0f2f1;border-color:#2a9d8f;border-bottom-style:dashed}
.elsewhere{background:#fde2c8;border-color:#e0700d;font-weight:bold}
.rounding{background:#fff6dc;border-color:#e0b040}
.stale{background:#ffe4b8;border-color:#e07000;font-weight:bold}
.untraced{background:#ffd6d6;border-color:#d00;font-weight:bold}
.count{background:#f0f0f0;border-color:#bbb;color:#555}
#legend{font:13px Helvetica,Arial,sans-serif;background:#f6f6f6;border:1px solid #ddd;padding:.6em 1em;margin-bottom:1em}
#legend span.n{margin-right:.8em}
#toc{font:13px Helvetica,Arial,sans-serif;columns:2;margin:1em 0 2em}
#toc a{text-decoration:none;color:#036} #toc .c{color:#888}
#toc .red{color:#d00;font-weight:bold} #toc .amb{color:#c60;font-weight:bold}
.secbar{font:12px Helvetica,Arial,sans-serif;color:#777;margin:-.4em 0 .6em}
.n{cursor:pointer}
.queued{outline:2px solid #6a4fd8;outline-offset:1px}
#pop{position:absolute;z-index:10;background:#fff;border:1px solid #999;box-shadow:0 4px 14px rgba(0,0,0,.2);padding:.6em .8em;width:400px;font:13px Helvetica,Arial,sans-serif;border-radius:4px}
#pop .pd{color:#555;margin:.3em 0 .5em;max-height:6em;overflow:auto;font-size:12px}
#pop label{display:block;margin:.3em 0}#pop input{width:100%;box-sizing:border-box;font:13px Helvetica,Arial,sans-serif;padding:.25em}
#pop .pb,#drawer .pb{margin-top:.5em}
#drawer{position:fixed;right:12px;bottom:12px;z-index:9;background:#f6f6f6;border:1px solid #ccc;padding:.5em .8em;max-width:360px;max-height:45vh;overflow:auto;font:12px Helvetica,Arial,sans-serif;border-radius:4px;box-shadow:0 2px 10px rgba(0,0,0,.15)}
#drawer .qi{margin:.2em 0}#drawer .ok{color:#2a7}#drawer .warn{color:#c60}
#qcount{background:#6a4fd8;color:#fff;border-radius:9px;padding:0 .5em}
@media (max-width:700px){
  body{font-size:16px;margin:.5em auto;padding:0 12px}
  #toc{columns:1}
  pre{font-size:11px}
  .n{padding:.1em .2em}
  #pop{position:fixed;left:0!important;right:0;bottom:0;top:auto!important;width:auto;border-radius:10px 10px 0 0;box-shadow:0 -4px 14px rgba(0,0,0,.25);font-size:15px}
  #pop input,#pop button,#drawer button,button{font-size:15px;padding:.4em .7em}
  #drawer{left:0;right:0;bottom:0;max-width:none;max-height:35vh;border-radius:10px 10px 0 0;font-size:14px}
  #drawer:empty{display:none}
  #legend{font-size:13px}
}
.src{color:#2a9d8f}
body.focus .traced,body.focus .deep,body.focus .unanchored,body.focus .rounding,body.focus .count{background:none;border-color:transparent;color:inherit;font-weight:inherit}
button{font:13px Helvetica,Arial,sans-serif}
"""

JS = r"""
function toggleFocus(){document.body.classList.toggle('focus');}

// ---- corrections: click a number, say what it should be, queue it ---------
// Two transports. Served by tools/proof_serve.py the queue POSTs to /__correct and
// lands in scratch/proof/corrections.jsonl, which the next session reads. Opened
// as a file:// it lives in localStorage and the drawer's "copy for chat" button
// gives you a block to paste. Either way nothing is processed until you say so.
const DOC = document.title.replace(/ — proof copy$/, '');
const KEY = 'proof_queue_' + DOC;
let served = false, dbq = null;   // dbq: the artifact's own store, when this page is a claude.ai artifact
function docOf(el){ const sec = el.closest('section.chapter'); return sec ? sec.dataset.doc : DOC; }
function sectionOf(el){ return el.dataset.sec || ''; }
function contextOf(span){ const p = span.closest('p,pre'); if(!p) return ''; const t = p.textContent; const i = t.indexOf(span.textContent); return t.slice(Math.max(0,i-80), i+span.textContent.length+80).replace(/\s+/g,' '); }
function load(){ try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch(e){ return []; } }
function save(q){ try { localStorage.setItem(KEY, JSON.stringify(q)); } catch(e){} }
function badge(){ const q = load(); const b = document.getElementById('qcount'); if (b) b.textContent = q.length; q.forEach(it => { const el = document.getElementById(it.id); if (el) el.classList.add('queued'); }); }
async function post(item){ try { const r = await fetch('/__correct', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(item)}); return r.ok; } catch(e){ return false; } }
function openPop(span){
  closePop();
  const pop = document.createElement('div'); pop.id = 'pop';
  const v = span.textContent, det = span.title;
  pop.innerHTML = `<div class=pt><b>${v}</b> <span class='n ${span.dataset.v}'>${span.dataset.v}</span></div>
    <div class=pd>${det.replace(/</g,'&lt;')}</div>
    <label>should read <input id=sug placeholder='value, or leave blank if only a note'></label>
    <label>note <input id=note placeholder='why / where it comes from'></label>
    <div class=pb><button id=qb>queue</button> <button onclick='closePop()'>cancel</button></div>`;
  document.body.appendChild(pop);
  const r = span.getBoundingClientRect();
  pop.style.top = (window.scrollY + r.bottom + 6) + 'px'; pop.style.left = Math.min(window.scrollX + r.left, window.innerWidth - 420) + 'px';
  document.getElementById('sug').focus();
  const submit = async () => {
    const item = { id: span.id, doc: docOf(span), section: sectionOf(span), value: v, verdict: span.dataset.v,
                   detail: det, context: contextOf(span), suggested: document.getElementById('sug').value.trim(),
                   note: document.getElementById('note').value.trim(), ts: new Date().toISOString() };
    if (!item.suggested && !item.note) return;
    item.done = false;
    const q = load(); q.push(item); save(q);
    if (served) await post(item);
    else if (dbq) { try { await dbq.add(item); } catch(e) { console.log('db add failed', e); } }
    closePop(); badge(); drawer();
  };
  document.getElementById('qb').onclick = submit;
  pop.addEventListener('keydown', e => { if (e.key === 'Enter') submit(); if (e.key === 'Escape') closePop(); });
}
function closePop(){ const p = document.getElementById('pop'); if (p) p.remove(); }
function drawer(){
  const q = load(); const d = document.getElementById('drawer');
  d.innerHTML = `<b>${q.length} queued</b> ${served ? '<span class=ok>· saved to scratch/proof/corrections.jsonl</span>' : dbq ? '<span class=ok>· saved in this artifact — Claude reads it next session</span>' : '<span class=warn>· held in this browser only — copy for chat</span>'}<br>` +
    q.map((it,i) => `<div class=qi><a href='#${it.id}'>${it.value}</a> → <b>${it.suggested || '(note)'}</b> <small>${it.section.slice(0,40)}</small> <button onclick='drop(${i})'>×</button></div>`).join('') +
    `<div class=pb><button onclick='copyQ()'>copy for chat</button> <button onclick='clearQ()'>clear</button></div>`;
}
function drop(i){ const q = load(); const it = q.splice(i,1)[0]; save(q); const el = document.getElementById(it.id); if (el) el.classList.remove('queued'); badge(); drawer(); }
function clearQ(){ if (!confirm('Clear the queue held in this browser? (the server copy, if any, is kept)')) return; load().forEach(it => { const el = document.getElementById(it.id); if (el) el.classList.remove('queued'); }); save([]); badge(); drawer(); }
function copyQ(){ const q = load(); const txt = 'PROOF CORRECTIONS\n' + q.map(it => `- [${it.doc} §${it.section}] "${it.value}" → ${it.suggested || '(no value)'}${it.note ? ' — ' + it.note : ''}\n    context: …${it.context}…`).join('\n'); navigator.clipboard.writeText(txt).then(() => alert('Copied ' + q.length + ' item(s) — paste into the chat.')); }
document.addEventListener('click', e => { const sp = e.target.closest('span.n'); if (sp) { e.preventDefault(); openPop(sp); } else if (!e.target.closest('#pop')) closePop(); });
function merge(items){ const q = load(); const ids = new Set(q.map(x => x.id + '@' + x.ts)); items.forEach(it => { if (!it.done && !ids.has(it.id + '@' + it.ts)) q.push(it); }); save(q); }
window.addEventListener('load', async () => {
  if (location.protocol !== 'file:') {
    try { const r = await fetch('/__queue?doc=' + encodeURIComponent(DOC)); if (r.ok) { served = true; merge(await r.json()); } } catch(e) {}
  }
  badge(); drawer();
  // a claude.ai artifact: the queue lives in the artifact's own store
  try {
    if (!served && window.claude && typeof claude.use === 'function') {
      const db = await claude.use('db');
      if (db) { dbq = db.collection('corrections'); const snap = await dbq.where('done', '==', false).limit(500).get(); merge(snap.docs.map(d => d.data())); badge(); drawer(); }
    }
  } catch(e) { console.log('no artifact db', e); }
});
"""

LEGEND = [("traced", "traced"), ("deep", "in a source CSV, unregistered"),
          ("elsewhere", "only OUTSIDE the section's sources"),
          ("rounding", "rounding (±1 last digit)"), ("stale", "stale"),
          ("untraced", "untraced"), ("count", "count")]


def paint(text: str, marks, secs, title: str, only_section: str | None, scope_map=None):
    """The mirror as HTML with the marks inserted."""
    # marks per line
    line_starts = [0]
    for m in re.finditer("\n", text):
        line_starts.append(m.end())
    import bisect
    by_line = defaultdict(list)
    for s, e, v, d in marks:
        ln = bisect.bisect_right(line_starts, s) - 1
        by_line[ln].append((s - line_starts[ln], e - line_starts[ln], v, d))
    sec_of_line = {}
    cur = ("", "(front matter)")
    for i in range(len(line_starts)):
        for ln, num, h in secs:
            if ln == i:
                cur = (num, h)
        sec_of_line[i] = cur
    # per-section counts
    counts = defaultdict(lambda: defaultdict(int))
    for ln, ms in by_line.items():
        for _, _, v, _ in ms:
            counts[sec_of_line[ln]][v] += 1
    lines = text.split("\n")
    body = []
    in_pre = False
    for i, line in enumerate(lines):
        sec = sec_of_line[i]
        if only_section and not (sec[0] == only_section or sec[0].startswith(only_section + ".")):
            continue
        if line.lstrip().startswith("<!--"):
            continue
        hm = _HEAD.match(line)
        if hm:
            if in_pre:
                body.append("</pre>"); in_pre = False
            lvl = len(hm.group(1))
            num, h = sec
            c = counts[sec]
            bar = " · ".join(f"<span class='{k}'>{c[k]} {LEGEND_NAME[k]}</span>"
                             for k in ("untraced", "stale", "elsewhere", "rounding", "traced", "deep", "unanchored", "count") if c[k])
            body.append(f"<h{lvl} id='s{num or i}'>{html.escape((num + ' ') if num else '')}{html.escape(h)}</h{lvl}>")
            sc, how = (scope_map or {}).get(sec, (set(), ""))
            srcs = ", ".join(sorted(pathlib.Path(x).name for x in sc)[:8]) + (" …" if len(sc) > 8 else "")
            src_line = (f"sources ({'proof_scope.csv' if how == 'file' else 'declared'}): {html.escape(srcs)}"
                        if sc else "sources: none declared — checked against everything")
            body.append(f"<div class=secbar>{bar or 'no numbers'}<br><span class=src>{src_line}</span></div>")
            continue
        painted = paint_line(line, by_line.get(i, []), f"{sec[0]} {sec[1]}".strip())
        is_table = line.startswith(("|", "+--", "  ---", "  ==")) or re.match(r"^\s{2,}\S.*\s{3,}\S", line)
        if is_table:
            if not in_pre:
                body.append("<pre>"); in_pre = True
            body.append(painted)
        else:
            if in_pre:
                body.append("</pre>"); in_pre = False
            if line.strip():
                body.append(f"<p>{painted}</p>")
    if in_pre:
        body.append("</pre>")
    tot = defaultdict(int)
    for c in counts.values():
        for k, n in c.items():
            tot[k] += n
    toc = []
    for ln, num, h in secs:
        c = counts[(num, h)]
        flag = (f" <span class=red>{c['untraced']} red</span>" if c["untraced"] else "") + \
               (f" <span class=amb>{c['stale'] + c['elsewhere']} amber</span>" if c["stale"] or c["elsewhere"] else "")
        toc.append(f"<div><a href='#s{num or ln}'>{html.escape(num)} {html.escape(h)}</a>"
                   f"<span class=c> ({sum(c.values())})</span>{flag}</div>")
    legend = " ".join(f"<span class='n {k}'>{LEGEND_NAME[k]}</span>" for k, _ in LEGEND)
    head = (f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width, initial-scale=1'>"
            f"<title>{html.escape(title)} — proof copy</title>"
            f"<style>{CSS}</style><script>{JS}</script><body>"
            f"<h1>{html.escape(title)} — proof copy</h1>"
            f"<div id=legend>{legend}<br>"
            f"<b>{tot['untraced']} untraced</b>, <b>{tot['stale']} stale</b>, <b>{tot['elsewhere']} elsewhere</b>, {tot['rounding']} rounding, "
            f"{tot['traced']} traced, {tot['deep']} in an unregistered CSV, {tot['unanchored']} unanchored, {tot['count']} counts. "
            f"Hover a number for what it was matched to. "
            f"<button onclick='toggleFocus()'>show only red / amber</button> "
            f"<span>click a number to queue a correction — <span id=qcount>0</span> queued</span><br>"
            f"<small>Generated by tools/proof_copy.py {__version__} from the committed mirror. "
            f"Green = a committed value with its anchor sits here, not a proof the sentence means that value.</small></div>"
            f"<div id=toc>{''.join(toc)}</div>")
    return (head + f"<section class=chapter data-doc='{html.escape(title)}'>" + "\n".join(body)
            + "</section><div id=drawer></div></body>"), counts


LEGEND_NAME = {"traced": "traced", "deep": "unregistered", "elsewhere": "ELSEWHERE", "unanchored": "unanchored", "rounding": "rounding",
               "stale": "STALE", "untraced": "UNTRACED", "count": "count"}


_SPAN_SEQ = [0]
_DOC_STEM = [""]


def paint_line(line: str, ms, sec: str = "") -> str:
    out, pos = [], 0
    for s, e, v, d in sorted(ms):
        out.append(html.escape(line[pos:s]))
        _SPAN_SEQ[0] += 1
        out.append(f"<span class='n {v}' id='n_{_DOC_STEM[0]}_{_SPAN_SEQ[0]}' data-v='{v}' data-sec='{html.escape(sec, quote=True)}' "
                   f"title='{html.escape(v + ': ' + d, quote=True)}'>"
                   f"{html.escape(line[s:e])}</span>")
        pos = e
    out.append(html.escape(line[pos:]))
    s = "".join(out)
    # light markdown: bold and the pandoc anchor junk
    s = re.sub(r"\[\]\{#[^}]*\}", "", s)
    s = re.sub(r"\\([^\\])", r"\1", s)               # pandoc's \' \~ \_ \< escapes
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)\{[^}]*\}", "<i>[figure]</i>", s)
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "<i>[figure]</i>", s)
    return s


# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("doc", nargs="+", help="report9, Paper1, Newborough_Methods_Supplement, or a path; several at once")
    ap.add_argument("--section", help="paint one section only, e.g. 4.2")
    ap.add_argument("--list", action="store_true", help="print the red/amber/orange list")
    ap.add_argument("--out", help="output directory (default scratch/proof)")
    ap.add_argument("--no-deep", action="store_true", help="registered values only; ~5 s faster")
    ap.add_argument("--bundle", action="store_true",
                    help="also write NRG_proof.html: every chapter generated so far in one page, for publishing")
    a = ap.parse_args()
    values = cc.collect_values()
    look = build_index(values, deep=not a.no_deep)
    out_dir = pathlib.Path(a.out) if a.out else OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in a.doc:
        one(name, values, look, out_dir, a)
    write_index(out_dir)
    if a.bundle:
        order = ["report", "report6", "report7", "report8", "report9", "report10", "report11", "report12",
                 "report13", "report14", "report15", "report16"]
        stems = [st for st in order if (out_dir / f"{st}.html").exists()] + \
                sorted(p.stem for p in out_dir.glob("*.html") if p.stem not in order and p.stem not in ("index", "NRG_proof"))
        b = write_bundle(out_dir, stems)
        print(f"  bundle {b.relative_to(REPO)} ({b.stat().st_size // 1024} KB, {len(stems)} chapters)")
    return 0


def one(name, values, look, out_dir, a):
    global TEXT_CACHE
    _SPAN_SEQ[0] = 0
    mirror = resolve_doc(name)
    _DOC_STEM[0] = mirror.stem
    rel = str(mirror.relative_to(REPO))
    text = mirror.read_text(encoding="utf8")
    TEXT_CACHE = text
    secs = section_numbers(mirror)
    scope_map = section_scope(text, secs, mirror.stem)
    idx = index_spans(mask_markup(text), rel, values)
    marks = add_corpus_echo(classify(text, look, idx, secs, scope_map), rel)
    page, counts = paint(text, marks, secs, mirror.stem, a.section, scope_map)
    (out_dir / f"{mirror.stem}.html").write_text(page, encoding="utf8")

    line_starts = [0] + [m.end() for m in re.finditer("\n", text)]
    rows = []
    for s, e, v, d in marks:
        if v not in ("untraced", "stale", "elsewhere"):
            continue
        ln = bisect.bisect_right(line_starts, s) - 1
        sec = ""
        for hl, num, h in secs:
            if hl <= ln:
                sec = f"{num} {h}".strip()
        ctx = " ".join(text[max(0, s - 70):e + 70].split())
        seckey = next(((num, h) for hl, num, h in reversed(secs) if hl <= ln), None)
        sc, how = scope_map.get(seckey, (set(), ""))
        scripts = ";".join(sorted({pathlib.Path(x).name.split("_")[0] for x in sc if re.match(r"\d\d", pathlib.Path(x).name)}))
        rows.append({"document": rel, "section": sec, "value": text[s:e],
                     "verdict": v, "scripts": scripts, "detail": d, "context": ctx})
    with open(out_dir / f"{mirror.stem}_untraced.csv", "w", encoding="utf8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["document", "section", "value", "verdict", "scripts", "detail", "context"])
        w.writeheader(); w.writerows(rows)

    tot = defaultdict(int)
    for c in counts.values():
        for k, n in c.items():
            tot[k] += n
    summary = (f"{sum(tot.values())} numbers — {tot['untraced']} UNTRACED, {tot['stale']} STALE, {tot['elsewhere']} ELSEWHERE, "
               f"{tot['rounding']} rounding, {tot['traced']} traced, {tot['deep']} unregistered-CSV, "
               f"{tot['count']} counts")
    (out_dir / f"{mirror.stem}.summary").write_text(summary, encoding="utf8")
    print(f"proof_copy {__version__}: {rel}\n  {summary}")
    print(f"  wrote {out_dir.relative_to(REPO) / (mirror.stem + '.html')} and "
          f"{mirror.stem}_untraced.csv ({len(rows)} rows)")
    if a.list:
        for r in rows:
            print(f"  [{r['verdict']:9}] §{r['section'][:28]:28} {r['value']:>10}  …{r['context'][:90]}…")


BUNDLE_JS = r"""
function showChapter(doc){
  document.querySelectorAll('section.chapter').forEach(sec => { sec.style.display = (sec.dataset.doc === doc) ? '' : 'none'; });
  document.querySelectorAll('#chapters a').forEach(a => a.classList.toggle('cur', a.dataset.doc === doc));
  try { localStorage.setItem('proof_bundle_chapter', doc); } catch(e) {}
  window.scrollTo(0, 0);
}
window.addEventListener('load', () => {
  let doc = (location.hash || '').replace(/^#c=/, '');
  try { doc = doc || localStorage.getItem('proof_bundle_chapter') || ''; } catch(e) {}
  const first = document.querySelector('section.chapter');
  showChapter(document.querySelector(`section.chapter[data-doc='${doc}']`) ? doc : (first ? first.dataset.doc : ''));
});
"""


def write_bundle(out_dir: pathlib.Path, stems: list[str], name: str = "NRG_proof"):
    """One page carrying every chapter generated so far, a chapter switcher, and
    the same click-to-queue. This is the file that travels: published as a
    claude.ai artifact with the db capability, its queue lives in the artifact's
    store and a session reads it with ArtifactData, laptop or no laptop."""
    sections, menu = [], []
    for st in stems:
        f = out_dir / f"{st}.html"
        if not f.exists():
            continue
        h = f.read_text(encoding="utf8")
        i = h.find("<section class=chapter"); j = h.rfind("</section>")
        if i < 0:
            continue
        sections.append(h[i:j + len("</section>")])
        sm = (out_dir / f"{st}.summary")
        summ = sm.read_text(encoding="utf8") if sm.exists() else ""
        m = re.search(r"(\d+) UNTRACED, (\d+) STALE, (\d+) ELSEWHERE", summ)
        red, amb = (int(m.group(1)), int(m.group(2)) + int(m.group(3))) if m else (0, 0)
        menu.append(f"<a href='#c={html.escape(st)}' data-doc='{html.escape(st)}' onclick=\"showChapter('{html.escape(st)}');return false;\">"
                    f"{html.escape(st)}" + (f" <span class=red>{red}</span>" if red else "") + (f" <span class=amb>{amb}</span>" if amb else "") + "</a>")
    legend = " ".join(f"<span class='n {k}'>{LEGEND_NAME[k]}</span>" for k, _ in LEGEND)
    page = (f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width, initial-scale=1'>"
            f"<title>{name} — proof copies</title><style>{CSS}"
            "#chapters{font:13px Helvetica,Arial,sans-serif;display:flex;flex-wrap:wrap;gap:.3em .6em;margin:.6em 0 1em}"
            "#chapters a{padding:.25em .6em;border:1px solid #ccc;border-radius:12px;text-decoration:none;color:#036;background:#fafafa}"
            "#chapters a.cur{background:#036;color:#fff;border-color:#036}#chapters .red{color:#f88;font-weight:bold}#chapters .amb{color:#fc8;font-weight:bold}"
            "#chapters a.cur .red{color:#ffb3b3}#chapters a.cur .amb{color:#ffe0a8}"
            f"</style><script>{JS}{BUNDLE_JS}</script><body>"
            f"<h1>{name} — proof copies</h1>"
            f"<div id=legend>{legend}<br>click a number to queue a correction — <span id=qcount>0</span> queued. "
            f"<button onclick='toggleFocus()'>show only red / amber</button><br>"
            f"<small>Generated by tools/proof_copy.py {__version__} from the committed mirrors. "
            f"Green = a committed value with its anchor sits here, not a proof the sentence means that value.</small></div>"
            f"<div id=chapters>{''.join(menu)}</div>"
            + "\n".join(sections) + "<div id=drawer></div></body>")
    (out_dir / f"{name}.html").write_text(page, encoding="utf8")
    return out_dir / f"{name}.html"


def write_index(out_dir: pathlib.Path):
    """scratch/proof/index.html — every proof copy generated so far, with totals."""
    rows = []
    for sm in sorted(out_dir.glob("*.summary")):
        stem = sm.stem
        txt = sm.read_text(encoding="utf8")
        m = re.search(r"(\d+) UNTRACED, (\d+) STALE(?:, (\d+) ELSEWHERE)?", txt)
        red, amb = (int(m.group(1)), int(m.group(2)) + int(m.group(3) or 0)) if m else (0, 0)
        import datetime
        when = datetime.datetime.fromtimestamp(sm.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        rows.append(f"<tr><td><a href='{stem}.html'>{html.escape(stem)}</a></td>"
                    f"<td class='{'red' if red else ''}'>{red}</td><td class='{'amb' if amb else ''}'>{amb}</td>"
                    f"<td>{html.escape(txt)}</td><td>{when}</td></tr>")
    page = (f"<!doctype html><meta charset=utf-8><title>proof copies</title><style>{CSS}"
            "table{border-collapse:collapse;font:13px Helvetica,Arial,sans-serif}td,th{border:1px solid #ddd;padding:.3em .6em;text-align:left}"
            ".red{color:#d00;font-weight:bold}.amb{color:#c60;font-weight:bold}</style><body>"
            "<h1>Proof copies</h1><p>One per document, regenerated by <code>python3 tools/proof_copy.py &lt;doc&gt; …</code>. "
            "Red = untraced numbers, amber = stale. Each page carries its own section index.</p>"
            "<table><tr><th>document</th><th>red</th><th>amber</th><th>summary</th><th>generated</th></tr>"
            + "".join(rows) + "</table></body>")
    (out_dir / "index.html").write_text(page, encoding="utf8")


if __name__ == "__main__":
    sys.exit(main())
