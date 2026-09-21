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

__version__ = "1.18.0"  # Hollingham (2026) — 2026-09-21. The reading pass is painted: eight
#   Sonnet subagents read every attributed number of the report (2,912 rows, brief in
#   scratch/reading/BRIEF.md) and their verdicts (tools/proof_reading_verdicts.csv) now
#   override the matcher — a DENIED attribution is red with the reader's reason and the
#   better source, a confirmed one says so, an unsure one is a tie. 843 of 2,912 were
#   denied (29 %): the honest measure of the digit-matcher, and the list of what to fix.
# v1.17.0  2026-09-21. After report8 part 1 of the reading pass
#   (Sonnet: 128 of 202 attributions denied). Formulas are masked — nothing inside
#   $…$ or $$…$$ is a citation (summation bounds, subscripts t−1, exponents had matched
#   config constants and cells); "1)" list markers are markers; a CSV CELL needs its ROW
#   named in the sentence — a column word alone ("rmse", "bias") had let any well's row
#   stand in for a Methods-chapter threshold; a quantity letter equal to 0 or 1 exactly
#   (r = 1, d = 0, NSE = 1) is definitional; a clause that cites a source outranks a
#   weak match (Stratford's 100–200 mm/yr, NRW's ±0.15 m are the literature's).
# v1.16.0  2026-09-20. After the reading pilot (Sonnet, 113
#   rows of the front matter, report6, report7: 15 denials, five patterns): a "%" token
#   no longer accepts a COEFFICIENT rendered as a percentage (24% had gone to α_B);
#   a registered key's ROW is its stem — ANCOVA_C_…_clearfell_step and …_clearfell_p are
#   one row, so a p beside its estimate takes the estimate's model, not a sibling
#   model's; the same-row bonus is decisive (+3) rather than a tie-breaker; "sites"
#   is a count word (~11 mm had gone to a count of Ranwell sites).
# v1.15.0  2026-09-20. Green is no longer a verdict without
#   a margin (Martin: "even the green ones you seem to be misattributing because you are
#   greping rather than reading"): every traced number carries its runner-up and the score
#   margin, and a margin of half a point or less is a TIE — a fourth colour, in the
#   red/amber focus view, so a near-coincidence is never hidden behind a confident green.
#   A one- or two-digit whole number cannot be a fraction rounded to nothing ("1" had
#   matched an ANOVA statistic of 0.629); "Phases 1--11", "Scripts 09--10" are labels.
# v1.14.0  2026-09-20. From the sixth queue (report7 §2,
#   the front matter): a literature citation in an EARLIER sentence of the same paragraph
#   still covers an untraced number ("The northern 700 hectares …" after Stratford et al.,
#   2007); "(about 0.6% of the plantation)" is the RATIO of two numbers in its own
#   sentence (4.4 / 700) and is painted as derived, not untraced; anchors match across a
#   word family ("scrapes" finds "scraping", "felled" finds "felling") so a key's words
#   are not missed on an inflection; a number whose sentence names the well and the
#   intervention now reaches 10m_report_numbers (WMC3 DiD steps) instead of Script 37.
# v1.13.0  2026-09-20. From the fifth queue (report6
#   §1, the front matter): a number is what the sentence makes it. A two-digit number
#   after "1951--" is a YEAR-RANGE END; "p. 17" is a PAGE; "SH 406 636" is a GRID
#   REFERENCE; "(1) … (2) …" are LIST MARKERS; "66-well" is a COUNT and no longer glued
#   to its noun. A number in a clause that carries an author-year citation and matches
#   no committed value is CITED (grey-blue), not untraced — "1,300 hectares (Stratford
#   et al., 2007)" is the literature's figure. The two ends of a range ("r 0.74--0.91")
#   and "n = 18" beside "r = 0.83" are LINKED: the second takes the first's file, and a
#   quantity letter other than p (n, r, R², k) is now checked against the neighbours'
#   row as p already was. "r 0.74" (no "=") is still an r; "n = 5" at the cluster scale
#   is the partition count.
# v1.12.0  2026-09-20. Linked to the PDFs: every
#   paragraph carries a "p.N" link to the page of the published PDF it is printed
#   on (tools/pdf_page_index.csv, built by tools/pdf_page_index.py from the PDF's
#   own text), every popover offers "open PDF p.N", and a Figure/Table/Section
#   reference opens the PDF at its TARGET's page. A paragraph the PDF build does
#   not contain is marked — the PDF is behind the text there. Martin: "would it
#   be possible to link the proof reading tool to the relevant parts of the pdfs?"
# v1.11.0  2026-09-20. Cross-references are painted
#   too: every "Figure N", "Table N", "Section x.y" and "§x.y" is resolved against
#   figure_map.csv, reference_index_table.csv and section_map.csv, and checked by
#   meaning the way ref_audit and section_ref_audit do — a script or PNG named in
#   the sentence must be the figure's own, a figure cited beside a § must live in
#   that section. The NUMBER_LEDGER and the symbol register are consulted: a red
#   number whose sentence matches a ledger row shows where the ledger says it
#   lives, and a number introduced by a registered glyph (β₃, λ, δ₀, τ…) is
#   admitted only from that sense's own keys, in that sense's units.
# v1.10.0  2026-09-20. Every red number carries its
#   HISTORY: the changelogs, decision log, working notes, ledgers and scripts are
#   indexed once, and a number no CSV holds shows where it has been discussed or
#   hard-coded, ranked by the words it shares with the sentence (Martin: "grep the
#   project chats and changelogs and decisions to pin down all the numbers").
#   Also: the page retires items the store marks done; sentence lookback fixed;
#   "±" is a magnitude; index-keyed rows weak; raw-input and matrix cells never
#   candidates; unscoped sections need outside evidence; the sentence's row or
#   script vouches for a weak candidate.
# v1.9.0  2026-09-20. Every match is TYPED. The
#   token gets a dimension from the unit beside it (°C, mm, m, %, ha, months, "p =",
#   "×") and a season from its clause; the candidate gets both from its column or
#   key name (_mm, _m, pct, temp, _p, months, summer). A KNOWN mismatch is a veto,
#   not a penalty: "+0.94°C" can no longer be a p-value, "+6.0 mm" cannot be
#   COAST_RETREAT_M, an "annual" figure cannot come from a summer column. Until
#   now the tool admitted any candidate with an anchor and bolted on one filter
#   per complaint (mm, %, ha, p =); this replaces those with one rule. Nominal
#   percentages ("above 100 %") are statements, not values.
# v1.8.0  2026-09-20. From the third artifact queue:
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


_QUANT_SYNONYMS = {"sd": ["standard deviation"], "std": ["standard deviation"], "se": ["standard error"], "stderr": ["standard error"],
                   "ci": ["confidence interval", "95%", "95 %"], "nse": ["efficiency"], "spread": ["spread", "range"],
                   "msl5": ["five-year", "msl5"], "window": ["five-year", "window"], "spring": ["spring"],
                   "rmse": ["root-mean-square", "rms"], "iqr": ["interquartile"], "cv": ["coefficient of variation"]}


def _anchor_sets(label: str):
    """(subject anchors, quantity anchors) for a registered key, cached: the same
    few thousand keys are asked about tens of thousands of times per chapter."""
    if label not in _ANCHOR_CACHE:
        subj, quant = cc.anchor_groups(label)
        quant = [q for q in quant if q.lower() not in WEAK_ANCHORS]
        # the prose's words for a column's abbreviations: "standard deviation" for sd,
        # "standard error" for se — report9 §4.8.3's SD/SE lists anchored on nothing
        quant = quant + [alt for q in list(quant) for alt in _QUANT_SYNONYMS.get(q.lower(), [])]
        if not quant and " · " in label:
            # cite_check found no quantity word in "reference / C1 · spring_sd_mm_median": read
            # the column's own tokens, through the synonyms (sd -> "standard deviation")
            for t in re.split(r"[_\W]+", label.rsplit(" · ", 1)[1]):
                tl = t.lower()
                if tl in _QUANT_SYNONYMS:
                    quant.extend(_QUANT_SYNONYMS[tl])
                elif len(tl) >= 4 and tl not in WEAK_ANCHORS and tl not in ("mean", "median"):
                    quant.append(tl)
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
    def present(k):
        fam = _FAMILY_OF.get(k)
        return (k in w) or (fam is not None and any(m in w for m in fam))
    if strict and subj and quant:
        return any(present(k) for k in subj) and any(present(k) for k in quant)
    return any(present(k) for k in subj) or any(present(k) for k in quant)


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
    "nse": ["nse", "efficiency"], "offset": ["offset", "bias-removed", "bias removed"], "r": ["r ", "(r", "correlation"],
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
    anc = {"col": ["k", "n", "clusters", "cluster", "partition", "clustering", "solution", "scale"], "file": [],
           "stat": ["k", "clusters", "cluster", "partition", "solution", "clustering", "identified", "five", "into", "scale"]}
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


_KML_SYNONYMS = {"clearfell": ["clearance", "clearfelled", "felled", "felling", "cleared"], "scrape": ["scraped", "scraping"],
                 "forest": ["plantation", "afforested", "pine"], "warren": ["dune", "dunes"], "restock": ["conversion", "broadleaf"]}
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
        # the prose's words for the same feature: "clearance", "felled", "felling" for the
        # clearfell polygon (report7 §2: "a partial clearance of approximately 4.4 ha")
        words += [alt for w in list(words) for alt in _KML_SYNONYMS.get(w, [])]
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
                if len(good) >= 3 and cw and not _CAND_DIM_RULES[0][1].search(c):
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
            scol = next((c for c in df.columns if c.lower() in ("season", "period", "window")), None)
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
            if (monthly and len(numcols) >= 10) or rel.startswith("data/"):
                continue                          # a wells-by-months matrix, or a raw input: its cells are never quoted, its statistics are (above)
            for _, r_ in df.iterrows():
                lab = str(r_[kcol])
                la = _label_anchors(lab)
                if ccol is not None:                  # "clearfell · C4": the row's cluster is part of its name
                    cl = str(r_[ccol]).strip()
                    mcl = re.search(r"[1-5]", cl)
                    if mcl and (cl.lower().startswith("c") or cl.replace(".0", "").isdigit()):
                        lab = f"{lab} · C{mcl.group()}"
                        la = la + CLUSTER_NAMES["c" + mcl.group()]
                if scol is not None:                  # "clearfell · annual · C4": and its season
                    sv = str(r_[scol]).strip().lower()
                    if sv in _SEASON_WORDS or sv in ("msl5", "spring"):
                        lab = f"{lab} · {sv}"
                        la = la + [sv]
                notew = [w for w in _deep_words(r_[notecol]) if len(w) >= 5 and w not in WEAK_ANCHORS][:12] \
                    if notecol is not None and isinstance(r_[notecol], str) else []
                rowvals = {}
                for c in df.columns[1:]:
                    if str(c).startswith("Unnamed"):
                        continue
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
_COUNT_COMPOUND = re.compile(r"(?i)^[\-‑](wells?|dipwells?|clusters?|sites?|stations?|members?|points?|boreholes?|months?|years?|days?)\b")   # "66-well network" is a count; "100-month" a duration
_YEAR_RANGE_BEFORE = re.compile(r"(?:18|19|20)\d\d\s*(?:--|–|—|-)\s*$")      # "1951--53": the 53 is a year
_PAGE_BEFORE = re.compile(r"(?i)\bpp?\.\s*(?:\d+\s*(?:--|–|—|-)\s*)?$")        # "p. 17", "pp. 17--19"
_GRIDREF = re.compile(r"\b[A-Z]{2}\s?\d{3}\s?\d{3}\b")                        # "SH 406 636"
_ENUM_MARK = re.compile(r"\(\d{1,2}\)")                                             # "(1) … (2) …"
_RANGE_BEFORE = re.compile(r"\d\s*(?:--|–|—|-|to)\s*$")
_ORDINAL_BEFORE = re.compile(r"(?i)\b(tiers?|sites?|phases?|steps?|scripts?|options?|batch(es)?|zones?|levels?|methods?|approach(es)?|types?|class(es)?|groups?|stages?|rounds?|parts?|panels?|checks?|objectives?|hypothes[ie]s|quadrats?|transects?|eras?|sketch(es)?|slacks?|models?|runs?|versions?)\s+(?:\d{1,2}[a-z]?\s*(?:--|–|—|-|,|and|to)\s*)*$")   # "Tier 1": a name                        # the second end of a range
_NOT_AUTHOR = r"(?!(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|Section|Figure|Table|Phase|Script|Since|Before|After|During|Until|From|In|By|Of|The|Between|Post|Pre|Winter|Summer|Spring|Autumn)\b)"
_CITATION = re.compile(_NOT_AUTHOR + r"[A-Z][A-Za-z'’\-]+(?:\s+(?:et al\.?|and|&)\s*[A-Z]?[A-Za-z'’\-]*)*,?\s*\(?(?:18|19|20)\d\d[a-z]?\)?"
                       r"|\((?:[^()]*?,\s*)?(?:18|19|20)\d\d[a-z]?(?:[;,][^()]*)?\)")   # "Stratford et al., 2007", "Ranwell (1959)", "(Davy et al., 2010, p. 17)"
_LIST_MARKER = re.compile(r"^\d+[.)]\s")
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
_QTY_BEFORE = re.compile(r"(?i)(?<![a-z0-9²_])(?:(p|r²|r2|r|n|k)\s*=\s*|(p|r²|r2|r)\s+)$")   # not m_P = 2.5; "(r 0.74" is an r
_QTY_PAT = {
    "p": re.compile(r"(?i)(^|_)(p|pval|pvalue|p_value|p_val|prob|significance)(_|$)|_p$|^p_"),
    "r": re.compile(r"(?i)(^|_)(r|rho|pearson|spearman|corr|correlation|affinity)(_|$)"),
    "r²": re.compile(r"(?i)(^|_)(r2|rsq|r_squared|rsquared|r²|adj_r2|r2_adj)(_|$)|r2|r_squared"),
    "n": re.compile(r"(?i)(^|_)(n|n_wells|n_obs|n_months|n_years|count|total|nobs|wells|columns|events)(_|$)|^n_|_n$|\bwell columns\b|dipwells|measuring points|distinct clusters"),   # "n = 5" at the cluster scale
    "k": re.compile(r"(?i)(^|_)(k|n_clusters|clusters)(_|$)|distinct clusters|clusters in"),
}


SYMBOLS = REPO / "tools" / "symbol_register.csv"
_SYMS: list | None = None
_GLYPH_BEFORE = re.compile(r"([βδλτκσφψξηαε][₀₁₂₃0-9]?|t½|Sy|R²)\s*(?:=|≈|of|is|~)\s*$")
_UNIT_DIM = {"m": "m", "mm": "mm", "m month-1": "m", "mm month-1": "mm", "mm yr-1": "mm", "m yr-1": "m", "mm/yr": "mm",
             "dimensionless": "ratio", "-": "ratio", "months": "duration", "month": "duration", "years": "duration",
             "m2 d-1": "", "d": "duration", "days": "duration", "%": "pct", "ha": "area"}


def _symbol_senses() -> list:
    global _SYMS
    if _SYMS is not None:
        return _SYMS
    out = []
    if SYMBOLS.exists():
        for r in csv.DictReader(SYMBOLS.open(encoding="utf8")):
            idents = {r.get("sense_id", "").strip().lower()}
            ctx = []
            for tok in (r.get("context_any") or "").split("|"):
                tok = tok.strip()
                if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{2,}", tok):
                    idents.add(tok.lower())
                elif tok:
                    ctx.append(tok.lower())
            out.append({"glyph": r.get("glyph", "").strip(), "sense": r.get("sense_id", "").strip(),
                        "idents": {i for i in idents if len(i) >= 3}, "ctx": ctx,
                        "units": (r.get("units") or "").strip(), "status": r.get("status", "")})
    _SYMS = out
    return out


def _symbol_gate(masked: str, s: int, clause: str):
    """(sense, admissible-key regex, dimension) when a registered glyph introduces the
    number ("β₃ = 0.089", "λ ≈ 230 m", "δ₀ = −31 mm/yr"); the sense is chosen by
    which sense's context words the clause carries. None when no glyph applies."""
    m = _GLYPH_BEFORE.search(masked[max(0, s - 12):s])
    if not m:
        return None
    g = m.group(1)
    base = g[0]
    senses = [x for x in _symbol_senses() if x["glyph"] == base or x["glyph"] == g]
    if not senses:
        return None
    low = clause.lower()
    senses.sort(key=lambda x: -sum(1 for c in x["ctx"] if c in low))
    best = senses[0]
    sub_ = g[1:] if len(g) > 1 and g[1] in "₀₁₂₃0123" else ""
    idents = set(best["idents"])
    if base == "β" and sub_:
        n = "₀₁₂₃".find(sub_) if sub_ in "₀₁₂₃" else int(sub_)
        idents = {f"beta_{n}", f"beta{n}", f"b{n}", f"beta_{n}_"}
    if base == "δ" and sub_ in ("₀", "0"):
        idents |= {"delta0", "delta_0", "coastal_decline"}
    if base == "λ":
        idents |= {"lambda", "reach"}
    if base == "τ":
        idents |= {"tau", "storage_drainage"}
    pat = re.compile("|".join(re.escape(i) for i in sorted(idents, key=len, reverse=True)), re.I) if idents else None
    return best["sense"], pat, _UNIT_DIM.get(best["units"], "")


def _qty_of(masked: str, s: int) -> str | None:
    m = _QTY_BEFORE.search(masked[max(0, s - 8):s])
    if not m:
        return None
    q = (m.group(1) or m.group(2)).lower()
    return "r²" if q in ("r2", "r²") else q


def _qty_ok(q: str, c: Cand) -> bool:
    pat = _QTY_PAT[q]
    col = c.col or (c.label.rsplit(" · ", 1)[1] if " · " in c.label else "")   # a registered "key · column"
    return bool(pat.search(col) or pat.search(c.label or ""))
COHERENCE_WINDOW = 260          # characters: a sentence and its neighbour


_MATH = re.compile(r"\$\$.*?\$\$|(?<!\$)\$(?!\$)[^$\n]{1,300}\$", re.S)


def mask_markup(text: str) -> str:
    f = lambda m: " " * len(m.group())
    # formulas are not citations: $h_{t-1}$, $$\sum_{m=1}^{12} …$$ carry indices and bounds
    return _MATH.sub(f, cc._IMGREF.sub(f, cc._MARKUP.sub(f, text))).replace("*", " ")


_WORD = re.compile(r"[a-z0-9²½₀₁₂₃βδλκτ]+")


_FAMILIES = [("scrap", ["scrape", "scrapes", "scraped", "scraping"]), ("fell", ["felled", "felling", "clearfell", "clearfelled"]),
             ("thin", ["thinning", "thinned"]), ("drain", ["drainage", "drained", "draining", "drains"]),
             ("rechar", ["recharge", "recharged", "recharging"]), ("interc", ["interception", "intercepted"]),
             ("flood", ["flood", "flooded", "flooding", "floods"]), ("retreat", ["retreat", "retreating", "retreated"])]
_FAMILY_OF = {m: fam for stem, fam in _FAMILIES for m in fam}


def _hit(a: str, w: str, ws: set) -> bool:
    """An anchor is present: whole-word for short anchors ("rec" must not match
    "record"), substring for longer ones (so "amplif" catches "amplification");
    a word family counts as one word ("scrapes" is "scraping" — report front
    matter, 2026-09-20)."""
    a = a.lower()
    if a in _FAMILY_OF:
        return any(m in ws for m in _FAMILY_OF[a])
    if len(a) <= 4 and " " not in a:
        return a in ws
    return a in w


_NONLEN = re.compile(r"(?i)pct|percent|ratio|fraction|_p$|pvalue|r2|rsq|count|_n$|index|years?|months?|days?")

# ---------------------------------------------------------------------------
# DIMENSIONS — what kind of quantity each side is
# ---------------------------------------------------------------------------
# Martin, 2026-09-20, after the fourth queue: "I have repeatedly said check units
# and context and you repeatedly make the same mistakes." Every earlier rule
# (mm, %, ha, "p =") was one unit bolted on after one complaint; a match is now
# admissible only when the dimension the TEXT gives the number and the dimension
# the CANDIDATE's own name gives its value are compatible. Unknown on either side
# is allowed (soft); a KNOWN mismatch is a veto.
_CAND_DIM_RULES = [
    ("id",       re.compile(r"(?i)(^|_)(id|cluster|cluster_k\d|k\d|code|well_id|match_id|date)(_|$)")),   # a label, never a quantity
    ("m",        re.compile(r"^(P|P_m|PET|PET_m|P_bar|PET_bar|P_(winter|summer|annual|total|w|s)|PET_(winter|summer|annual|total))$")),   # rainfall and PET in metres, before "P" reads as a p-value
    ("prob",     re.compile(r"(?i)(^|_)(p|pval|pvalue|p_value|p_val|prob|significance)(_|$)|_p$")),
    ("r2",       re.compile(r"(?i)(^|_)(r2|rsq|r_squared|rsquared|adj_r2|r2_adj)(_|$)|r²")),
    ("corr",     re.compile(r"(?i)(^|_)(r|rho|pearson|spearman|corr|correlation|affinity)(_|$)")),
    ("ratio",    re.compile(r"(?i)ratio|amplif|(^|_)amp(_|$)|(^|_)mult|factor|(^|_)x$|_scale|swing_ratio|(^|_)m_p$")),
    ("coef",     re.compile(r"(?i)beta|coef|(^|_)b[123]?(_|$)|intercept|gamma|lambda|kappa|alpha|delta0|(^|_)sy(_|$)|specific_yield|(^|_)nse|(^|_)d?nse|aic|bic|silhouette|stability")),
    ("pct",      re.compile(r"(?i)pct|percent|(^|_)share|fraction|proportion|(^|_)frac")),
    ("temp",     re.compile(r"(?i)temp|(^|_)t_mean|(^|_)c$|degc|°c|warming|anomaly|tmax|tmin|max_temp|min_temp")),
    ("area",     re.compile(r"(?i)area|(^|_)ha$|hectare")),
    ("volume",   re.compile(r"(?i)m3|m³|volume")),
    ("mm",       re.compile(r"(?i)(^|_)mm(_|$)|_mm$|mm_per|mm_yr|mm_month|(^|_)mm ")),
    ("m",        re.compile(r"(?i)(^|_)m(_|$)|_m$|_M$|_M(_|$)|metre|meter|(^|_)depth|(^|_)head|_wl|level|elevation|(^|_)dh_|(^|_)h_")),
    ("duration", re.compile(r"(?i)months?(_|$)|years?(_|$)|_yr$|(^|_)yr(_|$)|days?(_|$)|halflife|half_life|t_half|(^|_)tau|residence|recession_time|(^|_)lag")),
    ("count",    re.compile(r"(?i)(^|_)(n|count|total|n_wells|n_obs|nobs|wells|sites|events|columns|crossings|singletons)(_|$)|^n_|_n$|dipwells|measuring points|distinct clusters|_worsen$|_improve$")),
    ("stat",     re.compile(r"(?i)(^|_)(se|sd|stderr|std|ci_lo|ci_hi|ci)(_|$)|_se$|_sd$")),   # LAST: an unitless standard error is never "as %"; spring_sd_mm is mm
]
_PER_MONTH = re.compile(r"(?i)month|mo(_|$)")
_PER_YEAR = re.compile(r"(?i)_yr|yr(_|$)|year|per_a|a⁻¹")      # not "annual": that is a season word (the annual scenario is still per month)
_SEASON_WORDS = ("annual", "summer", "winter", "spring", "autumn")
_DIM_CACHE: dict[tuple, tuple] = {}


def _cand_dim(c: Cand) -> tuple:
    """(dimension, per, seasons) of a candidate from its own name. `per` is
    'month', 'yr' or ''. A registered key is read whole; a CSV cell reads its
    column first and its row label only for the season."""
    key = (c.rel, c.label, c.col, c.form, c.tier)
    hit = _DIM_CACHE.get(key)
    if hit is not None:
        return hit
    if c.tier == "geo":
        dim, per = "area", ""
    elif c.tier == "net":
        dim, per = "count", ""
    else:
        name = re.sub(r"[ ·/()]+", "_", c.col if c.col else c.label)
        dim = ""
        for d, rx in _CAND_DIM_RULES:
            if rx.search(name):
                dim = d
                break
        if not dim and c.col and c.tier in ("cell",):
            pass                                       # a row label says WHICH, not WHAT
        per = "month" if _PER_MONTH.search(name) else "yr" if _PER_YEAR.search(name) else ""
    if c.form == "mm":
        if dim in ("m", "", "stat"):
            dim = "mm"                                 # a length (or its standard error) in metres, rendered in mm
        # any other dimension keeps its name: a p-value "as mm" is still a p-value
    elif c.form == "%":
        if dim in ("", "ratio", "pct"):
            dim = "pct"                                # a fraction rendered as a percentage
        # a COEFFICIENT (β, α, Sy, NSE) rendered "as %" keeps its dimension and so clashes
        # with a "%" token: "24%" is FOREST_INTERCEPTION, not α_B = 0.237 (reading pilot)
        # a metre or a temperature rendered "as %" is nonsense: keep the base dimension
    low = (c.label + " " + (c.col or "")).lower()
    seasons = frozenset(sw for sw in _SEASON_WORDS if sw in low)
    hit = _DIM_CACHE[key] = (dim, per, seasons)
    return hit


_TOK_UNIT = [
    ("temp",     re.compile(r"^\s*(?:°\s*C|℃|deg\s*C|degrees)")),
    ("pct",      re.compile(r"(?i)^\s*(?:%|per cent|percent|percentage points)")),
    ("area",     re.compile(r"(?i)^\s*(?:ha|hectares?)\b")),
    ("volume",   re.compile(r"^\s*(?:m³|m3)\b")),
    ("mm",       re.compile(r"(?i)^\s*mm(?![a-z])")),
    ("cm",       re.compile(r"(?i)^\s*cm(?![a-z])")),
    ("km",       re.compile(r"(?i)^\s*km(?![a-z])")),
    ("m",        re.compile(r"(?i)^\s*m(?![a-z0-9³²])")),
    ("count",    re.compile(r"(?i)^\s*(?:(?:donor|focal|control|treatment|reference|extended|paired|matched|levelled|dip)\s+)?"
                            r"(?:wells?|dipwells?|sites?|stations?|boreholes?|clusters?|members?|events?|slacks?|hollows?|pipes?|piezometers?|observations?|readings?)\b"
                            r"|^[\-‑](?:wells?|dipwells?|clusters?|sites?|stations?|members?|points?|boreholes?)\b")),
    ("duration", re.compile(r"(?i)^\s*[\-‑]?(?:months?|years?|yrs?|days?|hours?)\b")),   # "100-month" is a duration too
    ("ratio",    re.compile(r"(?i)^\s*(?:×|x\b|-fold|times\b)")),
]
_LIST_UNIT = re.compile(r"^(?:\s*,\s*[+\-−]?\d[\d.]*(?:,\d{3})*)*(?:\s*,?\s*(?:and|to|--|–)\s*[+\-−]?\d[\d.]*(?:,\d{3})*)?\s*((?:mm|cm|km|m|%|ha|°C|months?|years?)\b)")
_TOK_PER = re.compile(r"(?i)^\s*(?:mm|m)\s*(?:w\.e\.)?\s*(?:/|per|·)?\s*(month|yr|year|a)\b|^\s*(?:mm|m)\s*(?:w\.e\.)?\s*(month|yr|a)⁻¹")
_QTY_DIM = {"p": "prob", "r": "corr", "r²": "r2", "n": "count", "k": "count"}


def _tok_dim(after: str, qty: str | None, clause: str, before: str) -> tuple:
    """(dimension, per, seasons) the TEXT gives a number: the unit after it, the
    quantity letter before it, and the season words of its clause (falling back
    to the paragraph only when the clause names none)."""
    dim, per = "", ""
    if qty:
        dim = _QTY_DIM.get(qty, "")
    else:
        for d, rx in _TOK_UNIT:
            if rx.match(after):
                dim = d
                break
        if not dim:
            # "78, 112, 141, 124 and 181 mm": the unit at the end of a list is every member's
            ml = _LIST_UNIT.match(after)
            if ml:
                for d, rx in _TOK_UNIT:
                    if rx.match(ml.group(1)):
                        dim = d
                        break
        m = _TOK_PER.match(after)
        if m:
            q = (m.group(1) or m.group(2) or "").lower()
            per = "month" if q.startswith("month") else "yr"
            if re.search(r"(?i)month", after[:24]) and re.search(r"(?i)yr|year|a⁻¹", after[:24]):
                per = ""                              # "mm month⁻¹ yr⁻¹": a trend in a monthly total — compound, unconstrained
    seasons = frozenset(sw for sw in _SEASON_WORDS if sw in clause)
    if not seasons and before:
        # the season the paragraph has ESTABLISHED before the number decides: the
        # nearest season word BEFORE it in the same paragraph ("net annual
        # responses … (C4 −12.2 mm)" is annual even when the next paragraph opens
        # with "the summer season"). `before` is the paragraph up to the number.
        found = {sw for sw in _SEASON_WORDS if sw in before}
        if len(found) == 1:
            seasons = frozenset(found)
        # a paragraph that has named MORE than one season ("net annual responses …
        # lower winter transpiration … (UKCP18 at C4: −6.2 …)") does not settle the
        # number's season: no constraint, and the candidate's own words decide
    return dim, per, seasons


def _dims_clash(tok: tuple, cand: tuple) -> str:
    """'' when compatible, else the reason. Unknown on either side is compatible."""
    td, tp, ts = tok
    cd, cp, cs = cand
    if cd == "id" and (td or tp):
        return "an identifier column"
    if td and cd and td != cd:
        return f"{td} vs {cd}"
    if tp and cp and tp != cp:
        return f"per {tp} vs per {cp}"
    if ts and cs and not (ts & cs):
        return f"{'/'.join(sorted(ts))} vs {'/'.join(sorted(cs))}"
    return ""
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


_SENT_END = re.compile(r"[.!?;]\s|\n")          # a CLAUSE: list items split at ';'
_FULL_END = re.compile(r"[.!?]\s|\n")           # a SENTENCE


_SCRIPT_PREFIX = re.compile(r"^(\d{2}[a-z]?)[_\s]")


def _script_of(rel: str) -> str:
    """The script an output belongs to: '20' for outputs/20_spatial_figures/20_msl5_…
    (Martin: 'it should trace to the previous figure's source' — a sentence's
    numbers come from one script's outputs even when from two of its files)."""
    name = pathlib.Path(rel).name
    m = _SCRIPT_PREFIX.match(name) or _SCRIPT_PREFIX.match(pathlib.Path(rel).parent.name)
    return m.group(1) if m else rel


def _derived_ratio(masked: str, s: int, e: int, marks) -> str:
    """"(about 0.6% of the plantation)": a percentage that is the ratio of two numbers
    earlier in its sentence (4.4 / 700). Returns the derivation, or ''."""
    if not _PCT_AFTER.match(masked[e:e + 12]):
        return ""
    try:
        x = float(_norm_num(masked[s:e]).replace(",", "").lstrip("+"))
    except ValueError:
        return ""
    lo = max(masked.rfind("\n", 0, s) + 1, s - 700)   # the paragraph so far: "700 hectares … 4.4 ha (about 0.6% of"
    nums = []
    for m in _NUM.finditer(masked, lo, s):
        try:
            v = float(_norm_num(m.group()).replace(",", "").lstrip("+"))
        except ValueError:
            continue
        if v > 0 and not _YEAR.match(_norm_num(m.group()).replace(",", "").lstrip("+-")):
            nums.append((m.group(), v))
    dp = _dp_of(_norm_num(masked[s:e]).lstrip("+-"))
    for i, (ta, a) in enumerate(nums):
        for tb, b in nums[i + 1:]:
            for num, den, tn, td in ((a, b, ta, tb), (b, a, tb, ta)):
                if den and abs(100 * num / den - x) <= 0.5 * 10 ** -dp + 1e-9:
                    return f"derived: {tn} / {td} = {100 * num / den:.{dp + 1}f} % — a ratio of two numbers in this paragraph"
    return ""


def _row_of(rel: str, lab: str) -> dict:
    """The cells of the row a candidate names. A REGISTERED candidate's label is
    "key · column" while ROWS is keyed on the key alone, so both are tried."""
    hit = ROWS.get((rel, lab))
    if hit is None and " · " in lab:
        hit = ROWS.get((rel, lab.rsplit(" · ", 1)[0]))
    return hit or {}


def _rowkey(label: str) -> str:
    """A row's name with its cluster removed, so 'thinning / annual / C4' and
    'thinning / annual / C5' count as the SAME row for the coherence pass: a
    sentence that quotes C4 then C5 from one scenario is reading one line of the
    table across."""
    out = _CLUSTER_ID.sub("", label)
    out = re.sub(r"(?i)\(?\b(lake edge|dune|western residual|main forest|coastal forest)\b\)?", "", out)
    # a registered key and its statistics are one row: ANCOVA_C_WMC3_only_Forest_clearfell_step,
    # …_clearfell_p, …_clearfell_se, …_ci_lo all read as the ANCOVA_C_… row
    out = re.sub(r"(?i)_(p|pvalue|p_value|step|slope|coeff|coef|se|sd|ci_lo|ci_hi|ci|t|r2|rsq|n|median|mean|min|max|lo|hi)$", "", out)
    return re.sub(r"\s+", " ", out).strip(" /·")


_SENT_CACHE: dict[tuple, str] = {}


def _sentence(masked: str, s: int, e: int, full: bool = False) -> str:
    hit = _SENT_CACHE.get((s, e, full))
    if hit is None:
        hit = _SENT_CACHE[(s, e, full)] = _sentence_uncached(masked, s, e, _FULL_END if full else _SENT_END)
    return hit


_SW_CACHE: dict[str, set] = {}


def _sent_words(sent: str) -> set:
    hit = _SW_CACHE.get(sent)
    if hit is None:
        if len(_SW_CACHE) > 4000:
            _SW_CACHE.clear()
        hit = _SW_CACHE[sent] = set(_WORD.findall(sent))
    return hit


def _sentence_uncached(masked: str, s: int, e: int, rx=None) -> str:
    """The clause the token sits in — from the previous sentence end (or ';' / ':',
    which in this corpus separate the items of a list) to the next. The anchor
    window is a paragraph wide, which is right for finding a key's words but
    wrong for choosing between keys: in the abstract every scenario name sits
    within 300 characters of every scenario number."""
    rx = rx or _SENT_END
    lo = max(0, s - 400)                   # a sentence longer than the lookback starts AT the lookback, not at the document
    for m in rx.finditer(masked, max(0, s - 400), s):
        lo = m.end()
    m2 = rx.search(masked, e, e + 400)
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
_LAST = [0.0]                                     # raw score of the last _accept call (for the weak list)
_INDEX_LABEL = re.compile(r"^[\d.\-–]+(\s|$)")


_LW_CACHE: dict[str, tuple] = {}


def _label_words(label: str) -> tuple:
    hit = _LW_CACHE.get(label)
    if hit is None:
        hit = _LW_CACHE[label] = tuple(wd for wd in set(_LABEL_WORD.findall(label.lower()))
                                       if wd not in cc._STOPWORDS and len(wd) >= 2)
    return hit


_CLUSTER_TOKENS = {"c1", "c2", "c3", "c4", "c5", "lake", "edge", "dune", "western", "residual", "main", "forest", "coastal"}


def _label_hits(label: str, w: str, ws: set, noncluster: bool = False) -> int:
    n = 0
    for wd in _label_words(label):
        if noncluster and wd in _CLUSTER_TOKENS:
            continue
        if wd in ws or (len(wd) >= 5 and wd in w):
            n += 1
    return n


def _accept(c: Cand, masked: str, s: int, e: int, short: bool, w: str, ws: set, inside: bool, scoped: bool = False,
            unit: str = "", tok: tuple | None = None) -> float:
    """Score a candidate at this position; 0 = not a citation. A registered value
    scores 3 when its key anchors here. A CSV cell scores 2 for its row label,
    1 for a column word, 0.5 for a file word; a derived statistic needs its
    column AND its statistic word; a rolling-mean extreme needs the column and
    'rolling'. In scope a short whole number needs 1, outside it needs 2; unit
    conversions (mm, %) lose 0.5 so a plain rendering wins a tie."""
    sent = _sentence(masked, s, e)
    if _cluster_clash(c, _sentence(masked, s, e, full=True)):
        return 0
    if tok is not None and _dims_clash(tok, _cand_dim(c)):
        return 0                              # "+0.94°C" is not a p-value; "+6.0 mm" is not a constant in metres
    if c.tier == "reg":
        weak = not cc.searchable(cc.render(abs(c.value), _dp_of(masked[s:e].lstrip("+-\u2212\u2013"))), c.label)
        _LAST[0] = 0.0
        if not anchored_here(masked, s, e, c.label, strict=weak or short, w=w):
            if (weak or short) and anchored_here(masked, s, e, c.label, strict=False, w=w):
                _LAST[0] = 1.5                # anchored, but not strictly: the neighbours' script may vouch for it
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
        score += 0.3 * min(5, _label_hits(c.label, sent, _sent_words(sent)))   # "SSM forward residual +73 mm": the key that says so
        if _clusters_in(c.label) and not _label_hits(c.label, w, ws, noncluster=True):
            score -= 1.5                          # "ceh20 · C4 · D_C4" anchored on nothing but the C4
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
        lab_hits = [x for x in a["label"] if _hit(x, w, ws)]
        if _INDEX_LABEL.match(c.label):
            # "2017 · change_mm", "1.0 · C5", "1969-10-01 · site_sd_m": a row keyed by a
            # year, a sweep value or a date. The text's "window end 2017" is a date,
            # not a citation of that row — worth 1 at most, 0.5 by its cluster alone
            score += 1 if any(x not in _CLUSTER_TOKENS for x in lab_hits) else 0.5 if lab_hits else 0
        elif any(x not in _CLUSTER_TOKENS and x not in CLUSTER_NAMES.get(x[:2], []) for x in lab_hits):
            score += 2
        elif lab_hits:
            score += 1                            # the row is named only by its cluster
        elif c.tier == "cell":
            _LAST[0] = 0.0
            return 0                              # a cell whose ROW the sentence never names is not a citation of it (report8 reading)
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
    _LAST[0] = score
    return score if score >= need else 0.0


WEAK: dict[tuple, list] = {}
OUTSIDE_OK: set = set()                    # registered candidates admitted from outside the declared scope


def classify(text: str, look: dict, idx: dict, secs, scope_map: dict):
    _SENT_CACHE.clear()
    WEAK.clear()
    OUTSIDE_OK.clear()
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
    chosen_idx = []       # (pos, rel, key) of numbers the citation index settled — they anchor their sentence too
    for m in _NUM.finditer(masked):
        s, e = m.start(), m.end()
        tok = m.group()
        if not cc._is_whole_number(masked, s, e) or not cc._citable_context(masked, s, e):
            continue
        if _GLUE_BEFORE.search(masked[max(0, s - 2):s]) or (_GLUE_AFTER.match(masked[e:e + 2]) and not _COUNT_COMPOUND.match(masked[e:e + 12])):
            continue
        if _GRIDREF.search(masked[max(0, s - 8):e + 8]) or _PAGE_BEFORE.search(masked[max(0, s - 12):s]):
            continue                                   # "SH 406 636"; "Davy et al., 2010, p. 17"
        if _IDENT_CHAIN.search(masked[max(0, s - 12):e + 12]) or re.search(r"(?i)\b(orcid|doi|isbn|issn|tel|epsg|grid ref(erence)?)\b", masked[max(0, s - 24):s]):
            continue                                   # ORCID 0000-0003-…, DOI 10.1016/…
        bol = masked.rfind("\n", 0, s) + 1
        if masked[bol:s].strip() == "" and _LIST_MARKER.match(masked[s:e + 2]):
            continue
        if (e - s) <= 2 and masked[e:e + 2] in (") ", ")\n") and masked[max(0, s - 2):s].strip() in ("", ";", ":") \
                and len(re.findall(r"(?:^|[;:]\s*)\d{1,2}\)\s", masked[bol:masked.find("\n", e) if masked.find("\n", e) > 0 else len(masked)], re.M)) >= 2:
            continue                                   # "1) … 2) … 3)": list markers mid-paragraph
        core = _norm_num(tok).replace(",", "")
        unsigned = core.lstrip("-")
        tok_text_plus = tok.startswith("+")
        if _YEAR.match(unsigned):
            continue
        if len(unsigned) == 2 and _YEAR_RANGE_BEFORE.search(masked[max(0, s - 8):s]):
            continue                                   # "1951--53", "1989--96": the second year
        if _ORDINAL_BEFORE.search(masked[max(0, s - 48):s]) and len(unsigned) <= 2 and "." not in unsigned:
            continue                                   # "Tier 1", "site 4": names, not values
        if len(unsigned) <= 2 and masked[max(0, s - 1):s] == "(" and masked[e:e + 1] == ")" \
                and len(_ENUM_MARK.findall(masked[bol:masked.find("\n", e) if masked.find("\n", e) > 0 else len(masked)])) >= 2:
            continue                                   # "(1) classify … (2) derive …": list markers
        scope, how = scope_map.get(sec_of(s), (set(), ""))
        row = idx_by_start.get(s)
        if row and (row["status"] == "confirmed" or row["verdict"] in ("traced", "rounding")):
            # A PROPOSED index row is a machine guess and mispoints inside tables
            # (CLAUDE.md §5): "3.57" in §4.2.2 was pointed at Script 25's δ₀ standard
            # error while the sentence quotes C3's β₁. A proposed row outside the
            # section's scope is ignored; a confirmed row is believed but noted.
            src = row["source_csv"]
            row_in = (not scope) or src in ALWAYS_IN_SCOPE or src in scope or str(pathlib.Path(src).parent) in scope
            _rc = Cand(src, row["key"], "", 0.0, None, "", "reg")
            _after0 = _RANGE_AFTER.sub("", masked[e:e + 64])
            if row["status"] != "confirmed" and (_cluster_clash(_rc, _sentence(masked, s, e, full=True))
                                                 or _dims_clash(_tok_dim(_after0, _qty_of(masked, s), _sentence(masked, s, e),
                                                                         masked[masked.rfind("\n", 0, s) + 1:s].lower()),
                                                                _cand_dim(_rc))):
                row = None                                 # a C3 key for a sentence about C4, or a p for a °C: not believed
            if row is not None and (row["status"] == "confirmed" or row_in):
                det = (f"{row['key']} · {pathlib.Path(src).name} · "
                       f"committed {row['committed']!r} · index {row['status']}"
                       + ("" if row_in else " — NB outside this section's sources"))
                prelim.append((s, e, row["verdict"], det, []))
                chosen_idx.append((s, src, row["key"]))
                continue
        if _qty_of(masked, s) and unsigned in ("0", "1", "0.0", "1.0", "0.00", "1.00"):
            prelim.append((s, e, "count", "definitional value (r = 1, NSE = 1, d = 0): a statement, not a measurement", []))
            continue
        if _NOMINAL_AFTER.match(masked[e:e + 24]):
            prelim.append((s, e, "count", "nominal scenario parameter (Martin: 'it doesn't trace')", []))
            continue
        bm = _BOUND_BEFORE.search(masked[max(0, s - 6):s])
        if bm:
            prelim.append((s, e, "bound", f"{(bm.group(1) or '').strip()} {bm.group(2)} {unsigned}", []))
            continue
        after = masked[e:e + 64]
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
        # a SIGNED number is not matched by a value of the opposite sign: "−12.2 mm"
        # is not a +12.18 slope, "+6.0 mm" is not a −5.95 projection (Martin, 2026-09-20)
        if core.startswith("-"):
            cands = [c for c in cands if c.value <= 0]
        elif tok_text_plus or masked[max(0, s - 1):s] == "±":
            cands = [c for c in cands if c.value >= 0]   # "+6.0" and "±25" are not matched by a negative value
        tok = _tok_dim(after, qty, _sentence(masked, s, e), masked[masked.rfind("\n", 0, s) + 1:s].lower())
        sym = _symbol_gate(masked, s, _sentence(masked, s, e))
        if sym:
            sense, spat, sdim = sym
            if spat:
                cands = [c for c in cands if spat.search((c.col or "") + " " + c.label)]
            if sdim and not tok[0]:
                tok = (sdim, tok[1], tok[2])              # the register's units stand in for a unit the text omits
        if "." in unsigned:
            # "6.0 mm" is not the integer 6 of a count or of a column nobody has typed:
            # a whole-number value matches a decimal rendering only when its own name
            # says it is a continuous quantity
            cands = [c for c in cands if not (float(c.value).is_integer() and _cand_dim(c)[0] in ("", "count", "id"))]
        if tok[0] == "count" and "." not in unsigned:
            cands = [c for c in cands if float(c.value).is_integer()]   # "11 donor wells" is not 11.4587 of anything
        if "." not in unsigned and len(unsigned) <= 2:
            # "1" is not an ANOVA statistic of 0.629 rounded to nothing, "11" is not −10.7,
            # "2 m" is not a canopy ratio of 1.51: a one- or two-digit whole number matches a
            # whole-number value, or a converted form ("−55 mm" from −0.0552 m)
            cands = [c for c in cands if float(c.value).is_integer() or c.form]
        if unsigned in ("0", "1") and not qty and not tok[0]:
            prelim.append((s, e, "count", "a bare 0 or 1: a statement, an index or a flag, not a value", []))
            continue
        if tok[0] == "pct" and re.match(r"(?i)\s*(?:%|per cent|percent)\s+of\b", masked[e:e + 14]):
            ratio = _derived_ratio(masked, s, e, prelim)
            if ratio:
                prelim.append((s, e, "count", ratio, []))   # "(about 0.6% of the plantation)" = 4.4 / 700
                continue
        if tok[0] == "pct" and re.match(r"(?i)\s*(?:%|per cent|percent)\s*(?:CI\b|confidence|credible|prediction interval)", masked[e:e + 24]):
            prelim.append((s, e, "count", "nominal confidence level — a statement, not a value", []))
            continue
        if tok[0] == "pct" and unsigned in ("100", "0"):
            prelim.append((s, e, "count", "nominal percentage — a statement, not a value", []))
            continue
        inside, outside, weak = [], [], []
        of_prev = None
        if re.search(r"\bof\s*$", masked[max(0, s - 4):s]) and prelim and prelim[-1][2] == "in" and abs(prelim[-1][1] - s) <= 12:
            of_prev = prelim[-1][4][0][1].rel if prelim[-1][4] else None
        for c in cands:
            if not scope or in_scope(c, scope) or c.tier in ("net", "geo"):   # a derived count or a KML area belongs to every section
                sc = _accept(c, masked, s, e, short, w, ws, bool(scope) or c.rel in ALWAYS_IN_SCOPE or c.tier in ("net", "geo", "reg"),
                             bool(scope), unit, tok)
            elif c.tier == "reg":
                # a REGISTERED key outside the section's declared sources is admitted when it
                # anchors on both its subject and its quantity (strictly, score 4+): the
                # declared scope comes from figure captions and misses the prose's sources
                # (§4.8.4 declares Script 03 while quoting Script 26's precision table)
                sc = _accept(c, masked, s, e, short, w, ws, True, True, unit, tok)
                if sc >= 4.0:
                    sc -= 0.3                          # a declared source of the same strength still wins
                    OUTSIDE_OK.add(id(c))
                else:
                    sc = 0
                    if _LAST[0] >= 1.0:
                        weak.append((_LAST[0], c))
                    continue
            else:
                continue
            if sc == 0 and of_prev and c.rel == of_prev and re.search(r"(?i)(^|_)(n|n_wells|total|count)(_|$)|n_wells|_n$", c.label):
                sc = 2                             # the N of "n of N", from the n's file
            if sc > 0:
                inside.append((sc, c))
            elif _LAST[0] >= 1.0:
                weak.append((_LAST[0], c))         # below the bar alone; the neighbours' script may vouch for it
        if not inside and len(cands) <= 4000:
            for c in cands:
                if scope and not in_scope(c, scope):
                    sc = _accept(c, masked, s, e, short, w, ws, False, unit=unit, tok=tok)
                    if sc > 0:
                        outside.append((sc, c))
        if inside:
            inside.sort(key=lambda t: (-t[0], t[1].tier != "reg"))
            if weak:
                WEAK[(s, e)] = weak                # considered again once the sentence's row is known
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
                            and anchored_here(masked, s, e, c.label, strict=True) \
                            and not _dims_clash(tok, _cand_dim(c)):
                        near = c
        if near:
            prelim.append((s, e, "rounding", f"one unit off {near.label} = {near.value:g} "
                                             f"[{pathlib.Path(near.rel).name}]", []))
            continue
        if short:
            prelim.append((s, e, "count", "whole number; no committed value to check against", weak))
            continue
        cites = ", ".join(sorted(pathlib.Path(x).name for x in scope)[:4]) if scope else "everything"
        what = f" as a {tok[0]}{' per ' + tok[1] if tok[1] else ''}" if tok[0] else ""
        prelim.append((s, e, "untraced", f"not in this section's sources ({cites}) at any precision{what}, "
                                         f"and anchored nowhere else", weak))

    # --- coherence pass: a sentence's numbers come from one row --------------
    chosen_rows = list(chosen_idx)       # (pos, rel, label); index-settled numbers count as the sentence's rows
    marks = []
    for s, e, v, d, options in prelim:
        if v in ("count", "untraced") and options:
            # Martin: "it should trace to the previous figure's source". A candidate
            # that fell short alone is accepted when the script its file belongs to is
            # the one the sentence's other numbers came from
            near_scripts = {_script_of(rel) for pos, rel, lab in chosen_rows if abs(pos - s) <= COHERENCE_WINDOW}
            vouched = [(sc, c) for sc, c in options if _script_of(c.rel) in near_scripts]
            if vouched:
                vouched.sort(key=lambda t: -t[0])
                options = vouched
                v, d = "in", ""
        if v == "in":
            near_rows = [(rel, _rowkey(lab)) for pos, rel, lab in chosen_rows if abs(pos - s) <= COHERENCE_WINDOW]
            # a candidate that fell short alone but sits in the ROW the sentence is
            # reading ("21--39 mm": the C4 cell of the row C1's 21 came from) outranks a
            # strongly-anchored key from elsewhere; one from the same SCRIPT is admitted
            near_scripts = {_script_of(r) for r, _ in near_rows}
            for wsc, wc in WEAK.get((s, e), []):
                if (wc.rel, _rowkey(wc.label)) in near_rows:
                    options = options + [(wsc + 3.0, wc)]
                elif _script_of(wc.rel) in near_scripts:
                    options = options + [(wsc + 2.0, wc)]
            if near_scripts:
                # Martin: "the previous figure's source governs the sentence". A candidate
                # from the sentence's script outranks one from anywhere else unless the
                # other is anchored in its own right (report6 §1: "r 0.74--0.91; efficiency
                # 0.32--0.80" had gone to Scripts 26, 31, 10 and 10d beside Script 44's −0.09)
                same_s = [(sc, c) for sc, c in options if _script_of(c.rel) in near_scripts]
                if same_s:
                    options = same_s + [(sc, c) for sc, c in options if _script_of(c.rel) not in near_scripts and sc >= 2.5]
            # "65 of 66 wells": the N belongs to the file the n came from (Martin:
            # "you should be referring to the previous number source when talking
            # about n out of N"), so a same-file candidate that reads as a total
            # outranks everything else for the number after "of"
            of_n = bool(re.search(r"\bof\s*$", masked[max(0, s - 4):s])) and chosen_rows and abs(chosen_rows[-1][0] - s) <= 12
            # "r 0.74--0.91": the second end of a range comes from the first end's file
            # (Martin: "if two numbers are separated by a - or + they are probably linked")
            range_prev = bool(_RANGE_BEFORE.search(masked[max(0, s - 6):s])) and chosen_rows and abs(chosen_rows[-1][0] - s) <= 14
            prev_rel = chosen_rows[-1][1] if (of_n or range_prev) else None
            if range_prev:
                for wsc, wc in WEAK.get((s, e), []):
                    if wc.rel == prev_rel and all(x[1] is not wc for x in options):
                        options = options + [(wsc + 2.0, wc)]
            ms_hint = ms_scripts(masked[s:e]) if len(options) > 1 else set()
            def key(t):
                sc, c = t
                same = (c.rel, _rowkey(c.label)) in near_rows
                samefile = any(r == c.rel for r, _ in near_rows)
                samescript = any(_script_of(r) == _script_of(c.rel) for r, _ in near_rows)
                bonus = (3.0 if same else 0.5 if samefile else 0.4 if samescript else 0) if sc >= 1.5 else 0
                if of_n and c.rel == prev_rel and re.search(r"(?i)(^|_)(n|n_wells|total|count)(_|$)|n_wells|_n$", c.label):
                    bonus += 3
                if range_prev and c.rel == prev_rel:
                    bonus += 2                       # the other end of the range, same file
                if c.tier == "net" and (d or ("." not in _norm_num(masked[s:e]) and len(_norm_num(masked[s:e]).lstrip("+-")) <= 3)):
                    bonus += 2                       # "k = 5", "66 wells": the network's own count outranks a column statistic that equals it
                if ms_hint and _script_of(c.rel) in ms_hint:
                    bonus += 1.5                     # the Methods Supplement quotes this number under that script
                return (-(sc + bonus), c.tier != "reg")
            options.sort(key=key)
            sc, c = options[0]
            chosen_rows.append((s, c.rel, c.label))
            verdict = "traced" if (c.tier == "reg" or c.rel in REG_FILES) else "deep"
            # the runner-up and the margin: a green with a rival half a point behind is a
            # coincidence as often as a citation, and the reader must see it (Martin, 2026-09-20)
            best_sc = -key(options[0])[0]
            # a rival carrying the SAME value (a consolidated copy, the same row in another
            # file) is not a rival: whichever is chosen, the sentence quotes that quantity
            rival = next(((t, -key(t)[0]) for t in options[1:]
                          if (t[1].rel, _rowkey(t[1].label)) != (c.rel, _rowkey(c.label))
                          and abs(t[1].value - c.value) > 1e-6 * max(1.0, abs(c.value))), None)
            margin = (best_sc - rival[1]) if rival else None
            base_verdict = verdict
            if rival is not None and margin <= 0.5:
                verdict = "tie"
            cite = _CITATION.search(_sentence(masked, s, e))
            if cite and best_sc < 3.5:
                # "(Stratford et al., 2006) … 100–200 mm/yr": a clause that cites a source and a
                # match that is not strongly anchored — the literature's figure, the match set aside
                marks.append((s, e, "cited", f"literature value — the clause cites {cite.group(0).strip()}; a weak match "
                                             f"({c.label}{(' · ' + c.col) if c.col else ''} = {c.value:g} [{pathlib.Path(c.rel).name}], score {best_sc:.1f}) was set aside"))
                chosen_rows.pop()
                continue
            same = (c.rel, _rowkey(c.label)) in near_rows
            det = (f"{c.label}{(' · ' + c.col) if c.col else ''} = {c.value:g} [{pathlib.Path(c.rel).name}]"
                   + (f" as {c.form}" if c.form else "")
                   + (" — same row as its neighbours" if same else "")
                   + (" — outside this section's declared sources, admitted on its own words" if id(c) in OUTSIDE_OK else "")
                   + (" — the other end of the range, from its file" if range_prev and c.rel == prev_rel else "")
                   + (f" — the Methods Supplement quotes it under Script {_script_of(c.rel)}" if ms_hint and _script_of(c.rel) in ms_hint else "")
                   + ("" if base_verdict == "traced" else
                      " — DERIVED from the file's geometry/columns; no script emits it (emit list)" if c.tier in ("net", "geo") else
                      " — UNREGISTERED: in no value table; register this file"))
            if rival is not None:
                rc = rival[0][1]
                det += (f" ‖ runner-up: {rc.label}{(' · ' + rc.col) if rc.col else ''} = {rc.value:g} [{pathlib.Path(rc.rel).name}]"
                        f" — margin {margin:.1f} ({best_sc:.1f} vs {rival[1]:.1f})"
                        + (" — A NEAR TIE: read the sentence, the tool cannot choose" if margin <= 0.5 else ""))
            else:
                det += " ‖ no rival candidate"
            marks.append((s, e, verdict, det))
        elif v in ("untraced", "count") and not options:
            ratio = _derived_ratio(masked, s, e, marks)
            cite = _CITATION.search(_sentence(masked, s, e))
            where = "clause"
            if not cite:
                # an earlier sentence of the SAME paragraph: "… (Stratford et al., 2007). The
                # northern 700 hectares were afforested …" (Martin: "Stratford 2007 again")
                bol = masked.rfind("\n", 0, s) + 1
                cite = _CITATION.search(masked[bol:s]); where = "paragraph"
            if ratio:
                marks.append((s, e, "count", ratio))
            elif cite and not (v == "count" and len(_norm_num(masked[s:e]).lstrip("-+")) <= 1):
                # "approximately 1,300 hectares … (Stratford et al., 2007)": the literature's
                # figure, not the pipeline's (Martin, 2026-09-20). Only when nothing traces.
                marks.append((s, e, "cited", f"literature value — the {where} cites {cite.group(0).strip()}; no committed value carries it"))
            else:
                marks.append((s, e, v, d))
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
        # the same sentence, NEAREST number first: "Forest (p < 0.001, R² = 0.885)" — the
        # R² twelve characters on is the p's row, not the previous cluster's p
        near = [(rel, lab) for pos, rel, lab in sorted(chosen_rows, key=lambda t: abs(t[0] - s)) if abs(pos - s) <= 150]
        found = None
        if what in ("n", "r", "r²", "k") and op == "=":
            # "r = 0.83, n = 18": the n of the row the r came from (Martin, 2026-09-20)
            qpat = _QTY_PAT[what]
            for rel, lab in near:
                for col, val in _row_of(rel, lab).items():
                    if qpat.search(col) and isinstance(val, (int, float)):
                        found = (rel, lab, col, val); break
                if found:
                    break
        if what == "p":
            clause_w = _sent_words(_sentence(masked, s, e))
            for rel, lab in near:
                pcols = [(col, val) for col, val in _row_of(rel, lab).items() if _PCOL.match(col)]
                if not pcols:
                    continue
                # several p columns (p_value_P_winter, p_value_h_min): the one whose own
                # words the clause uses, else the one that satisfies the bound, else the first
                def _pw(col):
                    return len(clause_w & set(_LABEL_WORD.findall(col.lower().replace("p_value", "").replace("pvalue", ""))))
                pcols.sort(key=lambda cv: -_pw(cv[0]))
                if op != "=" and len(pcols) > 1:
                    # a row with several p columns: the bound holds if any of them satisfies
                    # it, and the detail names which — a STALE verdict needs every p to fail
                    sat = [cv for cv in pcols if ((cv[1] < b) if op in "<≤" else (cv[1] > b))]
                    if sat:
                        pcols = sat + [cv for cv in pcols if cv not in sat]
                col, val = pcols[0]
                found = (rel, lab, col, val)
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
    # --- a range is one quantity: "70--100 cm (Jennings, 1990)" — the second end takes the
    # --- first end's literature verdict rather than a rounding coincidence of its own
    for i in range(1, len(out)):
        s0, e0, v0, d0 = out[i - 1]
        s1, e1, v1, d1 = out[i]
        if v0 == "cited" and v1 in ("rounding", "count", "untraced", "deep") and s1 - e0 <= 6 \
                and _RANGE_BEFORE.search(masked[max(0, s1 - 6):s1]):
            out[i] = (s1, e1, "cited", d0 + " — the other end of the range")
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
.cited{background:#eceaf6;border-color:#8f86c9;color:#444;border-bottom-style:dotted}
.tie{background:#f3f0c8;border-color:#b8a500;font-weight:bold;border-bottom-style:double}
.denied{background:#ffd6d6;border-color:#a00;font-weight:bold;border-bottom-style:double}
.xref{background:#e8eefc;border-color:#6d8fe6;border-bottom-style:dotted}
a.pg{font:10px Helvetica,Arial,sans-serif;color:#6d8fe6;text-decoration:none;margin-right:.5em;vertical-align:super;white-space:nowrap}
a.pgno{color:#c60}
#pop .pl{margin-top:.4em;font-size:12px}
.xbad{background:#ffd6d6;border-color:#d00;font-weight:bold;border-bottom-style:double}
.xmean{background:#fde2c8;border-color:#e0700d;border-bottom-style:double}
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
body.focus .traced,body.focus .deep,body.focus .unanchored,body.focus .rounding,body.focus .count,body.focus .cited{background:none;border-color:transparent;color:inherit;font-weight:inherit}
button{font:13px Helvetica,Arial,sans-serif}
"""

JS = r"""
function toggleFocus(){document.body.classList.toggle('focus');}
// the published PDFs: GitHub Pages when this page is hosted, the repo's own copy when
// it is served from scratch/proof/ or opened as a file (two levels up)
const PAGES_BASE = 'PAGES_BASE_PLACEHOLDER';
function pdfUrl(rel){ const local = (location.protocol === 'file:' || /^(127\.|localhost|192\.168\.|10\.)/.test(location.hostname)); return (local ? '../../' : PAGES_BASE) + rel; }
document.addEventListener('click', e => { const a = e.target.closest('a.pg'); if (a && a.dataset.pdf) { e.preventDefault(); window.open(pdfUrl(a.dataset.pdf), '_blank', 'noopener'); } });

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
    ${span.dataset.pdf ? `<div class=pl><a href="${pdfUrl(span.dataset.pdf)}" target=_blank rel=noopener>open the PDF at this page ↗</a></div>` : ''}
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
// the store is the truth about what has been PROCESSED: an item a session marked
// done there leaves this browser's queue too (Martin, 2026-09-20: "the page
// doesn't clear my previous flags")
function retire(doneItems){ const gone = new Set(doneItems.map(x => x.id + '@' + x.ts)); const q = load().filter(it => !gone.has(it.id + '@' + it.ts)); load().forEach(it => { if (gone.has(it.id + '@' + it.ts)) { const el = document.getElementById(it.id); if (el) el.classList.remove('queued'); } }); save(q); }
window.addEventListener('load', async () => {
  if (location.protocol !== 'file:') {
    try { const r = await fetch('/__queue?doc=' + encodeURIComponent(DOC)); if (r.ok) { served = true; const items = await r.json(); retire(items.filter(it => it.done)); merge(items); } } catch(e) {}
  }
  badge(); drawer();
  // a claude.ai artifact: the queue lives in the artifact's own store
  try {
    if (!served && window.claude && typeof claude.use === 'function') {
      const db = await claude.use('db');
      if (db) {
        dbq = db.collection('corrections');
        const all = (await dbq.limit(1000).get()).docs.map(d => d.data());
        // the store is the truth: whatever it no longer holds as open — marked done,
        // or deleted when a session cleared the queue — leaves this browser too
        const open = new Set(all.filter(it => !it.done).map(it => it.id + '@' + it.ts));
        retire(load().filter(it => !open.has(it.id + '@' + it.ts)));
        merge(all.filter(it => !it.done));
        badge(); drawer();
      }
    }
  } catch(e) { console.log('no artifact db', e); }
});
"""

LEGEND = [("traced", "traced"), ("deep", "in a source CSV, unregistered"),
          ("elsewhere", "only OUTSIDE the section's sources"),
          ("rounding", "rounding (±1 last digit)"), ("stale", "stale"),
          ("untraced", "untraced"), ("count", "count"), ("cited", "literature value (the clause cites a source)"),
          ("tie", "NEAR TIE — two candidates within half a point; read the sentence"),
          ("denied", "DENIED by the reading pass — the sentence does not quote the attributed quantity"),
          ("xref", "cross-reference resolves"), ("xmean", "cross-reference points at the WRONG thing"),
          ("xbad", "cross-reference does not resolve")]


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
                             for k in ("denied", "untraced", "stale", "elsewhere", "tie", "rounding", "traced", "deep", "unanchored", "count", "cited") if c[k])
            body.append(f"<h{lvl} id='s{num or i}'>{html.escape((num + ' ') if num else '')}{html.escape(h)}</h{lvl}>")
            sc, how = (scope_map or {}).get(sec, (set(), ""))
            srcs = ", ".join(sorted(pathlib.Path(x).name for x in sc)[:8]) + (" …" if len(sc) > 8 else "")
            src_line = (f"sources ({'proof_scope.csv' if how == 'file' else 'declared'}): {html.escape(srcs)}"
                        if sc else "sources: none declared — checked against everything")
            body.append(f"<div class=secbar>{bar or 'no numbers'}<br><span class=src>{src_line}</span></div>")
            continue
        pg = page_of_line(_DOC_STEM[0], line)
        href = pdf_href(_DOC_STEM[0], pg)
        painted = paint_line(line, by_line.get(i, []), f"{sec[0]} {sec[1]}".strip(), href)
        if href:
            painted = f"<a class=pg data-pdf='{html.escape(href, quote=True)}' href='#' title='this paragraph is on page {pg} of the published PDF'>p.{pg}</a>" + painted
        elif line.strip() and _page_index().get(_DOC_STEM[0]) and len(_para_fp(line)) >= 24 and not line.startswith(("|", "  ", "!")):
            painted = "<a class='pg pgno' href='#' title='this paragraph is not in the published PDF as built — the PDF is behind the text here'>p.?</a>" + painted
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
            f"<style>{CSS}</style><script>{JS.replace('PAGES_BASE_PLACEHOLDER', PAGES_BASE)}</script><body>"
            f"<h1>{html.escape(title)} — proof copy</h1>"
            f"<div id=legend>{legend}<br>"
            f"<b>{tot['denied']} denied by the reading pass</b>, <b>{tot['untraced']} untraced</b>, <b>{tot['stale']} stale</b>, <b>{tot['elsewhere']} elsewhere</b>, <b>{tot['tie']} near-ties</b>, {tot['rounding']} rounding, "
            f"{tot['traced']} traced, {tot['deep']} in an unregistered CSV, {tot['unanchored']} unanchored, {tot['count']} counts, {tot['cited']} literature. "
            f"Hover a number for what it was matched to. "
            f"<button onclick='toggleFocus()'>show only red / amber</button> "
            f"<span>click a number to queue a correction — <span id=qcount>0</span> queued</span><br>"
            f"<small>Generated by tools/proof_copy.py {__version__} from the committed mirror. "
            f"Green = a committed value with its anchor sits here, not a proof the sentence means that value.</small></div>"
            f"<div id=toc>{''.join(toc)}</div>")
    return (head + f"<section class=chapter data-doc='{html.escape(title)}'>" + "\n".join(body)
            + "</section><div id=drawer></div></body>"), counts


LEGEND_NAME = {"traced": "traced", "deep": "unregistered", "elsewhere": "ELSEWHERE", "unanchored": "unanchored", "rounding": "rounding",
               "stale": "STALE", "untraced": "UNTRACED", "count": "count", "cited": "cited", "tie": "NEAR-TIE", "denied": "DENIED",
               "xref": "xref", "xmean": "XREF-MEANING", "xbad": "XREF-BAD"}


_SPAN_SEQ = [0]
_DOC_STEM = [""]


_PDF_TAG = re.compile(r" @@pdf=([^@]*)@@")


def paint_line(line: str, ms, sec: str = "", pdf: str = "") -> str:
    out, pos = [], 0
    for s, e, v, d in sorted(ms):
        out.append(html.escape(line[pos:s]))
        _SPAN_SEQ[0] += 1
        tm = _PDF_TAG.search(d)
        own = tm.group(1) if tm else pdf                  # a reference opens its target's page; a number its own
        d = _PDF_TAG.sub("", d)
        out.append(f"<span class='n {v}' id='n_{_DOC_STEM[0]}_{_SPAN_SEQ[0]}' data-v='{v}' data-sec='{html.escape(sec, quote=True)}' "
                   + (f"data-pdf='{html.escape(own, quote=True)}' " if own else "")
                   + f"title='{html.escape(v + ': ' + d, quote=True)}'>"
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


# ---------------------------------------------------------------------------
# the written record: where a red number has been discussed before
# ---------------------------------------------------------------------------
# Martin, 2026-09-20: "you are going to have to grep the project chats and
# changelogs and decisions to pin down all the numbers". A number no CSV carries
# usually has a history — the changelog that introduced it, the decision that set
# it, the script whose comment or literal holds it. That history is indexed once
# and attached to every red number's tooltip and work-list row, so the reader
# sees where it came from before deciding what should emit it.
HISTORY_GLOBS = ("working/changelogs/*.md", "working/updates/*.md", "working/DECISION_LOG.md",
                 "working/WORK_REGISTER.md", "working/PROJECT_DIARY.md", "notes/**/*.md",
                 "DECISIONS_PUBLIC.md", "CLAUDE.md", "src/*.py", "src/utils/*.py",
                 "docs/report/text/Newborough_Methods_Supplement.md", "docs/papers/paper_1/text/PAPER1_SI_methods.md")
# Martin, 2026-09-20: "using the methods supplement would also resolve the origins of some
# of the numbers". The Supplement documents each script's method and declares its
# sources, so a sentence of it that quotes the same number and names a file or a
# script is the number's provenance, and is shown first.
HISTORY_MAX = 3
_HIST: dict[str, list] | None = None
_HIST_NUM = re.compile(r"(?<![\w.\-])\d[\d,]*\.\d+|(?<![\w.\-])\d{3,}(?![\w.])")


def _history_index() -> dict:
    """rendering -> [(file, snippet)] over the written record, built once."""
    global _HIST
    if _HIST is not None:
        return _HIST
    idx: dict[str, list] = defaultdict(list)
    for g in HISTORY_GLOBS:
        for p in sorted(REPO.glob(g)):
            if not p.is_file() or p.stat().st_size > 2_000_000:
                continue
            try:
                txt = p.read_text(encoding="utf8", errors="ignore")
            except OSError:
                continue
            rel = str(p.relative_to(REPO))
            seen = set()
            for m in _HIST_NUM.finditer(txt):
                key = m.group().replace(",", "")
                if key in seen or _YEAR.match(key) or len(key.replace(".", "")) < 3:
                    continue
                seen.add(key)
                snip = " ".join(txt[max(0, m.start() - 70):m.end() + 50].split())
                if "Methods_Supplement" in rel or "SI_methods" in rel:
                    # the Supplement's sentence, and the source it declares or the script it names
                    a = max(txt.rfind(". ", 0, m.start()), txt.rfind("\n", 0, m.start())) + 1
                    b = txt.find(". ", m.end()); b = len(txt) if b < 0 else b + 1
                    sent = txt[a:b]
                    src = _SRC_RE.search(txt[a:min(len(txt), b + 400)]) or _SRC_RE.search(txt[max(0, a - 1500):b])
                    scr = _SCRIPT_RE.search(sent)
                    where = (f" → {src.group(1).strip()}" if src else "") + (f" [Script {scr.group(1)}]" if scr else "")
                    snip = " ".join(sent.split())[:160] + where
                idx[key].append((rel, snip))
    _HIST = idx
    return idx


LEDGER = REPO / "notes" / "ledgers" / "NUMBER_LEDGER.md"
_LEDGER: list | None = None


def _ledger_rows() -> list:
    """(id, quantity, source, cited_in, notes, words) from NUMBER_LEDGER.md's tables."""
    global _LEDGER
    if _LEDGER is not None:
        return _LEDGER
    rows = []
    if LEDGER.exists():
        for line in LEDGER.read_text(encoding="utf8").splitlines():
            if not line.startswith("| N-"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 4:
                continue
            nid, qty, src = cells[0], cells[1], cells[2]
            notes = cells[5] if len(cells) > 5 else ""
            words = {w for w in _WORD.findall((qty + " " + notes).lower()) if len(w) >= 5 and w not in cc._STOPWORDS}
            rows.append((nid, qty, src, cells[4] if len(cells) > 4 else "", notes, words))
    _LEDGER = rows
    return rows


def ledger_of(clause: str) -> str:
    """The NUMBER_LEDGER row whose quantity the sentence is talking about, if any:
    where the ledger says this number LIVES (Martin: "don't we have a number and
    symbols ledger?"). Two shared content words or more; the best row only."""
    cw = {w for w in _WORD.findall(clause.lower()) if len(w) >= 5 and w not in cc._STOPWORDS}
    best = None
    for nid, qty, src, cited, notes, words in _ledger_rows():
        k = len(cw & words)
        if k >= 2 and (best is None or k > best[0]):
            best = (k, nid, qty, src)
    if not best:
        return ""
    k, nid, qty, src = best
    return f" ‖ ledger {nid}: {qty} — lives in {src}"


_MS_SCRIPT = re.compile(r"\[Script (\d{2}[a-z]?)\]")


def ms_scripts(value: str) -> set:
    """The scripts the Methods Supplement names in sentences quoting this number."""
    key = _norm_num(value).replace(",", "").lstrip("-")
    return {m.group(1) for f, snip in _history_index().get(key, [])
            if ("Methods_Supplement" in f or "SI_methods" in f) for m in _MS_SCRIPT.finditer(snip)}


def history_of(value: str, clause: str = "") -> str:
    key = _norm_num(value).replace(",", "").lstrip("-")
    hits = _history_index().get(key, [])
    if not hits:
        return ""
    # a snippet that shares the sentence's own words ("wet area", "study area") is
    # the number's history; one that merely contains the digits is a coincidence.
    # Changelogs and decisions before notes and scripts; the proof-copy changelog
    # itself last, since it quotes every red number it discusses
    cw = {w for w in _WORD.findall(clause.lower()) if len(w) >= 5 and w not in cc._STOPWORDS}
    order = {"docs/report/text/Newborough_Methods_Supplement.md": -1, "docs/papers/paper_1/text/PAPER1_SI_methods.md": -1,
             "working/changelogs": 0, "working/DECISION_LOG.md": 1, "working/updates": 2, "notes": 3}
    def rank(h):
        f, s = h
        shared = len(cw & {w for w in _WORD.findall(s.lower()) if len(w) >= 5})
        selfref = 1 if ("proof_copy" in f or "HANDOVER_NOTE" in f or "HANDOFF_" in f) else 0
        return (-shared, selfref, next((v for k, v in order.items() if f.startswith(k)), 5))
    hits = sorted(hits, key=rank)
    shown = hits[:HISTORY_MAX]
    more = f" (+{len(hits) - HISTORY_MAX} more)" if len(hits) > HISTORY_MAX else ""
    return " ‖ history: " + " | ".join(
        (f"Methods Supplement: {s}" if "Methods_Supplement" in f else f"Paper 1 SI: {s}" if "SI_methods" in f
         else f"{pathlib.Path(f).name}: …{s}…") for f, s in shown) + more


# ---------------------------------------------------------------------------
# the published PDF: which page each paragraph, figure, table and heading is on
# ---------------------------------------------------------------------------
PAGE_INDEX = REPO / "tools" / "pdf_page_index.csv"
PAGES_BASE = "https://newbroman.github.io/Newborough_Hydrology/"   # GitHub Pages serves the repo
_PAGES: dict | None = None
_PARA_MARKUP = re.compile(r"!\[[^\]]*\]\([^)]*\)(\{[^}]*\})?|\[\]\{#[^}]*\}|\{[^}]*\}|\*\*|\\(.)")


def _page_index() -> dict:
    """{doc: {"para": {fp24: page}, "heading": {...}, "figure": {...}, "table": {...},
    "pdf": rel, "built": iso}} from tools/pdf_page_index.csv (pdf_page_index.py)."""
    global _PAGES
    if _PAGES is not None:
        return _PAGES
    idx: dict = {}
    if PAGE_INDEX.exists():
        for r in csv.DictReader(PAGE_INDEX.open(encoding="utf8")):
            d = idx.setdefault(r["document"], {"para": {}, "heading": {}, "figure": {}, "table": {},
                                               "pdf": r["pdf"], "built": r["pdf_built"]})
            d[r["kind"]][r["key"]] = int(r["page"])
    _PAGES = idx
    return idx


def _para_fp(line: str) -> str:
    return re.sub(r"[^a-z0-9]", "", _PARA_MARKUP.sub(lambda m: m.group(2) or "", line).lower())[:24]


def page_of_line(doc: str, line: str) -> int:
    d = _page_index().get(doc)
    return d["para"].get(_para_fp(line), 0) if d else 0


def page_of_target(kind: str, key: str) -> int:
    """A figure's or table's page in the report PDF; a section's page is its first
    paragraph's (the heading index carries the heading text, so look it up by number
    through section_map)."""
    rep = _page_index().get("report") or {}
    if kind in ("figure", "table"):
        return rep.get(kind, {}).get(str(key).rstrip("abcd"), 0)
    if kind == "section":
        row = _xref_tables()["sec"].get(key)
        if not row:
            return 0
        stem = pathlib.Path(row.get("document", "")).stem
        d = _page_index().get(stem) or {}
        return d.get("heading", {}).get(row.get("heading", ""), 0)
    return 0


def pdf_href(doc: str, page: int) -> str:
    d = _page_index().get(doc)
    return f"{d['pdf']}#page={page}" if d and page else ""


# ---------------------------------------------------------------------------
# cross-references: does "Figure 27" exist, and is it the figure the sentence means?
# ---------------------------------------------------------------------------
# Martin, 2026-09-20: "the other thing that needs adding to the proof reading tool
# is the cross references". Resolution comes from the maps the reference gates
# already keep (figure_map.csv from each caption's Source: marker, reference_index_
# table.csv, section_map.csv). Meaning is checked the way ref_audit and
# section_ref_audit do, on evidence the sentence itself carries: a script id or
# PNG named in the sentence must be the cited figure's own; a figure cited in the
# same sentence as a §/Section must live in that section (an ancestor agrees).
FIG_MAP = REPO / "tools" / "figure_map.csv"
TAB_MAP = REPO / "tools" / "reference_index_table.csv"
_XREF = re.compile(r"(?<![A-Za-z])(Figures?|Figs?\.?|Tables?|Sections?|§)\s?(\d+(?:\.\d+)*[a-d]?)"
                   r"((?:\s*(?:--|–|—|-|,|and|&)\s*\d+(?:\.\d+)*[a-d]?)*)")
_XREF_ITEM = re.compile(r"\d+(?:\.\d+)*[a-d]?")
_XREF_RANGE = re.compile(r"(\d+)([a-d]?)\s*(?:--|–|—|-)\s*(\d+)([a-d]?)")
_SCRIPT_MENTION = re.compile(r"(?i)\bscript\s+(\d{2}[a-z]?)\b|\b(\d{2}[a-z]?)_[a-z0-9_]+\.(?:py|png|jpg|csv)\b")
_XREF_SEP = re.compile(r"\s*(?:--|–|—|-|,|\band\b|&)\s*")
_XREF_TABLES: dict | None = None


def _xref_tables() -> dict:
    global _XREF_TABLES
    if _XREF_TABLES is not None:
        return _XREF_TABLES
    figs, tabs, secs = {}, {}, {}
    if FIG_MAP.exists():
        for r in csv.DictReader(FIG_MAP.open(encoding="utf8")):
            figs[r["number"].strip()] = r
    if TAB_MAP.exists():
        for r in csv.DictReader(TAB_MAP.open(encoding="utf8")):
            tabs[r["number"].strip()] = r
    if SECTION_MAP.exists():
        for r in csv.DictReader(SECTION_MAP.open(encoding="utf8")):
            secs[r["number"].strip()] = r
    _XREF_TABLES = {"fig": figs, "tab": tabs, "sec": secs}
    return _XREF_TABLES


def _fig_script(row) -> str:
    m = re.match(r"(\d{2}[a-z]?)_", pathlib.Path(row.get("source") or "").name)
    return m.group(1) if m else ""


def xref_marks(text: str, masked: str, taken: list) -> list:
    """(s, e, verdict, detail) for every cross-reference; `taken` spans (numbers
    already painted) inside a reference are dropped by the caller."""
    T = _xref_tables()
    out = []
    for m in _XREF.finditer(masked):
        kind = m.group(1).lower()
        if kind.startswith("fig") and re.search(r"(?i)\bscript\s*$", masked[max(0, m.start() - 8):m.start()]):
            continue                                           # "script figures 21-03": a pipeline output id
        if re.match(r"[a-z_0-9]", masked[m.end():m.end() + 1]):
            continue                                           # "figure 14b_year_crossing.csv": a filename
        bol = masked.rfind("\n", 0, m.start()) + 1
        if masked[bol:m.start()].strip() == "" and masked[m.start():m.start() + 12].startswith(m.group(1)) \
                and re.match(r"\s*:", masked[m.end():m.end() + 3]):
            continue                                           # a caption's own "Figure N:" — not a reference
        sent = _sentence(masked, m.start(), m.end(), full=True)
        # the numbers this reference names, ranges expanded
        items = []
        rest = m.group(2) + (m.group(3) or "")
        toks = [x for x in _XREF_SEP.split(rest) if x]
        seps = _XREF_SEP.findall(rest)
        for i, tk in enumerate(toks):
            items.append(tk)
            # "Figures 7--9": an integer range expands; "Sections 4.8.1--4.8.2" names its two ends
            if i + 1 < len(toks) and i < len(seps) and re.search(r"--|–|—|-", seps[i]) \
                    and tk.isdigit() and toks[i + 1].isdigit() and 0 < int(toks[i + 1]) - int(tk) <= 12:
                items += [str(k) for k in range(int(tk) + 1, int(toks[i + 1]))]
        items = list(dict.fromkeys(items))
        verdict, det = "xref", ""
        parts = []
        for it in items:
            if kind.startswith("fig"):
                row = T["fig"].get(it.rstrip("abcd")) or T["fig"].get(it)
                if not row:
                    verdict = "xbad"; parts.append(f"Figure {it}: no such figure in figure_map.csv"); continue
                cap = (row.get("caption") or "")[:90]
                src = pathlib.Path(row.get("source") or "").name
                p = f"Figure {it} → §{row.get('section', '')} ({row.get('document', '')}) · {cap} · {src}"
                # meaning: a script or PNG the sentence names must be this figure's
                own = _fig_script(row)
                # the script mentioned in the SAME CLAUSE, a preceding mention first (ref_audit's
                # rule: the governing script precedes its figure; a following one counts only
                # when nothing precedes) — never a mention from the next sentence
                cl_lo = max(0, m.start() - 400)
                for cm in _SENT_END.finditer(masked, cl_lo, m.start()):
                    cl_lo = cm.end()
                cm2 = _SENT_END.search(masked, m.end(), m.end() + 400)
                cl_hi = cm2.start() if cm2 else m.end() + 400
                before = [(m.start() - mm.end(), g) for mm in _SCRIPT_MENTION.finditer(masked, cl_lo, m.start()) for g in mm.groups() if g]
                after_ = [(mm.start() - m.end(), g) for mm in _SCRIPT_MENTION.finditer(masked, m.end(), cl_hi) for g in mm.groups() if g]
                near = sorted(before) or sorted(after_)
                if near and own:
                    named = {g for _d, g in near}
                    if own in named or (len(own) > 2 and own[:2] in named) or any(g.startswith(own) for g in named):
                        pass
                    else:
                        verdict = "xmean" if verdict != "xbad" else verdict
                        p += f" — but the sentence names Script {near[0][1]} beside it and this figure is Script {own}'s"
                parts.append(p)
            elif kind.startswith("tab"):
                key = it.rstrip("abcd")
                row = T["tab"].get(key)
                note = ""
                if not row and re.match(r"^1\.\d+$", key):
                    row = T["tab"].get(key[2:])                    # "Table 1.4a": the caption's chapter-numbered form of Table 4
                    note = " (written in the caption's chapter-numbered form; the text elsewhere says Table N)"
                if not row:
                    verdict = "xbad"; parts.append(f"Table {it}: no such table in reference_index_table.csv"); continue
                parts.append(f"Table {it} ({row.get('document', '')}) · {(row.get('title') or '')[:90]}{note}")
            else:
                row = T["sec"].get(it)
                if not row:
                    verdict = "xbad"; parts.append(f"Section {it}: no such heading in section_map.csv"); continue
                p = f"Section {it} → {row.get('heading', '')} ({row.get('document', '')})"
                # meaning: a figure cited in the same sentence lives in this section (or a descendant)
                # only "(Section 4.9.6, Figure 50)" — the two inside ONE bracket — pairs them;
                # a figure merely nearby is another sentence's business
                loc = masked[max(0, m.start() - 40): m.end() + 40]
                paired = re.findall(r"(?i)\(\s*sections?\s+" + re.escape(it) + r"\s*[,;]\s*figures?\s+(\d{1,3})(?!\d)", loc) \
                    + re.findall(r"(?i)\(\s*figures?\s+(\d{1,3})\s*[,;]\s*sections?\s+" + re.escape(it) + r"(?![\d.])", loc)
                for fig in paired:
                    fm = type("M", (), {"group": (lambda self, i=1, f=fig: f)})()
                    frow = T["fig"].get(fm.group(1))
                    if not frow:
                        continue
                    fsec = frow.get("section", "")
                    if fsec.split(".")[0] != it.split(".")[0]:
                        continue                              # a methods section beside a results figure: not compared
                    if not (fsec == it or fsec.startswith(it + ".") or it.startswith(fsec + ".")):
                        verdict = "xmean" if verdict != "xbad" else verdict
                        p += f" — but Figure {fm.group(1)}, cited beside it, lives in §{fsec}"
                parts.append(p)
        if not parts:
            continue
        det = "; ".join(parts)
        # the TARGET's page in the report PDF, for the popover's "open PDF" link
        tkind = "figure" if kind.startswith("fig") else "table" if kind.startswith("tab") else "section"
        tp = page_of_target(tkind, items[0]) if items else 0
        if tp:
            det += f" @@pdf={pdf_href('report', tp)}@@"
        out.append((m.start(), m.end(), verdict, det))
    return out


READING_VERDICTS = REPO / "tools" / "proof_reading_verdicts.csv"
_READ: dict | None = None


def reading_verdicts() -> dict:
    """id -> (verdict, reason, better) from the reading pass, built once."""
    global _READ
    if _READ is None:
        _READ = {}
        if READING_VERDICTS.exists():
            with READING_VERDICTS.open(encoding="utf8") as fh:
                for r in csv.DictReader(fh):
                    _READ[r["id"]] = (r["verdict"], r.get("reason", ""), r.get("better", ""), r.get("attribution_read", ""))
    return _READ


def _reading_id(num: str, sentence: str, offset: int) -> str:
    """A stable id for a number in its sentence: survives regeneration, moves only
    when the sentence or the number changes. The offset separates repeats."""
    import hashlib
    return hashlib.sha1(f"{num}|{sentence[:160]}|{offset}".encode("utf8")).hexdigest()[:10]


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
    _m = mask_markup(text)
    marks = [(s, e, v, d + (history_of(text[s:e], _sentence(_m, s, e)) if v in ("untraced", "elsewhere", "stale", "tie") else "")
              + (ledger_of(_sentence(_m, s, e)) if v in ("untraced", "elsewhere", "stale", "count") else ""))
             for s, e, v, d in marks]
    # the reading pass overrides the matcher: a person (or a subagent reading as one)
    # decided whether the sentence quotes the attributed quantity
    rv = reading_verdicts()
    if rv:
        new_marks = []
        for s, e, v, d in marks:
            if v in ("traced", "deep", "tie"):
                sent_full = " ".join(_sentence(_m, s, e, full=True).split())
                rid = f"{mirror.stem}:{_reading_id(text[s:e], sent_full, s - _m.rfind(chr(10), 0, s))}"
                hit = rv.get(rid)
                if hit:
                    verdict, reason, better, read_attr = hit
                    # a verdict is about the attribution the reader SAW: when the matcher has
                    # since chosen a different key or file, the denial does not carry over
                    cur = d.split(" ‖ ")[0].split(" — ")[0]
                    def _key(a):
                        return re.sub(r"\s*=\s*[-−+\d.eE]+", "", a).replace("read: confirmed ✓ — ", "").strip()[:120]
                    same_attr = (not read_attr) or _key(read_attr) == _key(cur) or (read_attr.rsplit("[", 1)[-1] == cur.rsplit("[", 1)[-1] and read_attr[:25] == cur[:25])
                    if verdict == "deny" and not same_attr:
                        d = d + f" ‖ an earlier attribution ({read_attr[:80]}) was denied by the reading pass; this is a new one, unread"
                    elif verdict == "deny":
                        v, d = "denied", (f"DENIED by the reading pass — {reason}" + (f" — better: {better}" if better else "")
                                          + " ‖ the matcher had: " + d.split(" ‖ ")[0])
                    elif verdict == "confirm":
                        v = "traced" if v in ("traced", "tie") and "UNREGISTERED" not in d else v
                        d = "read: confirmed ✓ — " + d
                    else:
                        v, d = "tie", f"reading pass unsure — {reason} ‖ " + d
            new_marks.append((s, e, v, d))
        marks = new_marks
    xm = xref_marks(text, _m, marks)
    if xm:
        spans = [(s, e) for s, e, _v, _d in xm]
        marks = [mk for mk in marks if not any(s <= mk[0] and mk[1] <= e for s, e in spans)]
        marks = sorted(marks + xm)
    page, counts = paint(text, marks, secs, mirror.stem, a.section, scope_map)
    (out_dir / f"{mirror.stem}.html").write_text(page, encoding="utf8")

    line_starts = [0] + [m.end() for m in re.finditer("\n", text)]
    rows = []
    for s, e, v, d in marks:
        if v not in ("untraced", "stale", "elsewhere", "xbad", "xmean", "denied"):
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
    # the READING list: every number the tool attributed (green, teal, tie), with the
    # whole sentence and the runner-up, for a reader — a person or a subagent — to
    # confirm or deny the attribution (Martin, 2026-09-20: "you are greping rather
    # than reading the sense around the numbers")
    rrows = []
    for i, (s, e, v, d) in enumerate(marks):
        if v not in ("traced", "deep", "tie"):
            continue
        ln = bisect.bisect_right(line_starts, s) - 1
        sec = ""
        for hl, num, h in secs:
            if hl <= ln:
                sec = f"{num} {h}".strip()
        parts = d.split(" ‖ ")
        sent_full = " ".join(_sentence(_m, s, e, full=True).split())
        rid = f"{mirror.stem}:{_reading_id(text[s:e], sent_full, s - _m.rfind(chr(10), 0, s))}"
        rrows.append({"id": rid, "section": sec, "number": text[s:e], "verdict": v,
                      "attribution": parts[0][:400],
                      "runner_up": next((x for x in parts[1:] if x.startswith("runner-up")), "")[:300],
                      "sentence": sent_full[:700]})
    with open(out_dir / f"{mirror.stem}_reading.csv", "w", encoding="utf8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "section", "number", "verdict", "attribution", "runner_up", "sentence"])
        w.writeheader(); w.writerows(rrows)

    tot = defaultdict(int)
    for c in counts.values():
        for k, n in c.items():
            tot[k] += n
    summary = (f"{sum(tot.values()) - tot['xref'] - tot['xbad'] - tot['xmean']} numbers — {tot['denied']} DENIED, {tot['untraced']} UNTRACED, {tot['stale']} STALE, {tot['elsewhere']} ELSEWHERE, {tot['tie']} NEAR-TIES, "
               f"{tot['rounding']} rounding, {tot['traced']} traced, {tot['deep']} unregistered-CSV, "
               f"{tot['count']} counts; {tot['xref'] + tot['xbad'] + tot['xmean']} cross-references — "
               f"{tot['xbad']} unresolved, {tot['xmean']} pointing at the wrong thing")
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
            f"</style><script>{JS.replace('PAGES_BASE_PLACEHOLDER', PAGES_BASE)}{BUNDLE_JS}</script><body>"
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
