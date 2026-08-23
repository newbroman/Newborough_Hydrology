#!/usr/bin/env python3
"""
cite_check.py
=============
Standing check that the document corpus still agrees with the committed
pipeline outputs.

tools/audit_number_drift.py is CHANGE-triggered: it diffs two git refs and
hunts for renderings of the value that just changed. It cannot see a number
that went stale before anyone was watching — which is how report9 and Paper 1
both carried five superseded cluster coefficients for weeks while the tooling
reported clean.

This tool is STANDING: it asks, of every value the pipeline currently publishes,
whether the corpus still quotes it — and, where it does not, whether the corpus
quotes a NEAR MISS instead. A near miss is the signature of a stale citation:
0.090 where the CSV now says 0.088, VIF 1.11 where it says 1.09.

It also evaluates a small register of CLAIMS — the assertions that carry no
number and so no numeric tool can check. "C4 has the lowest VIF in the network"
is either true of the committed CSV or it is not; the register makes that
machine-decidable and names every document asserting it.

Usage:
    python3 tools/cite_check.py                  # numbers + claims
    python3 tools/cite_check.py --claims-only
    python3 tools/cite_check.py --dp 2 3 4 --near 2
"""
from __future__ import annotations

__version__ = "1.10.0"  # Hollingham (2026) — 2026-08-22. near_misses() was
#   generating the value's own rendering as a near miss of itself. It excluded
#   k = 0 but not the STRING: 2.0865 renders at 3 dp as "2.087", and so does
#   2.0865 + 0.001, because in binary that sum is 2.08749999999999991. Every
#   document quoting such a number CORRECTLY was reported as drifted. This is
#   the bulk of what made the triage list unreadable (M23).
#
# v1.9.0  # Hollingham (2026) — 2026-08-22. The sweep could tell
#   whether the corpus quotes the COMMITTED value. It could not tell whether the
#   corpus quotes the SAME value in every document, and that is the question that
#   bit: the forest reach was quoted at 220, 223, 225, 228 and 230 m across five
#   documents while the figure rendered 226 and the CSV held 226.442. None of
#   those matched at any searched precision, so the quantity sat in the "not
#   cited anywhere" bin, which is exactly where every deliberately-rounded prose
#   figure lives and where nothing had ever looked.
#
#   Two changes, both asked for by Martin on 2026-08-22:
#     (a) values of magnitude >= LARGE_VALUE_MIN are also searched at dp = 0, so
#         a quantity of order hundreds is findable in the form prose writes it;
#     (b) a new SPREAD check — for a registered quantity, collect EVERY rendering
#         near its anchor across the whole corpus and report the distinct set.
#         It fires on disagreement between documents, whether or not any of the
#         renderings matches the CSV, which is the case the other checks cannot
#         see. Advisory unless --spread-gate.
#
# v1.8.0  # Hollingham (2026) — 2026-08-21. EXTRA_VALUE_TABLES —
#   the third hole. collect_values() reads only *report_numbers*.csv, so any
#   script publishing into the documents without one was never checked at all.
#   Twenty-four output directories carry CSVs and no report-numbers file; the
#   register names the ones whose numbers are quoted, starting with Script 15,
#   which was stale in four of five values and had flipped a published ranking
#   while the gate stayed green.
#
# v1.7.0  # Hollingham (2026) — 2026-08-21. Manifest counts are
#   registered only where a phrase anchor exists. A small integer without one
#   cannot be distinguished from a step index, so the sub-step counts and
#   analytical_phases — the latter cited in no document by standing rule — were
#   reporting every occurrence of "11", "13" and "15" in the corpus as a stale
#   count. Checking a number badly is worse than not checking it: it fills the
#   triage list with noise and the real hits stop being read.
#
# v1.6.1  # Hollingham (2026) — 2026-08-21. The tier and exec
#   phrases needed the number in them. "analytical" and "default pass" sit
#   beside step indices as well as counts — "steps 36-41/50, all analytical-
#   default" — so the loose phrases matched indices and reported 38 and 41 as
#   stale counts. Every manifest phrase now pins {n}.
#
# v1.6.0  # Hollingham (2026) — 2026-08-21. Phrase anchors for the
#   manifest counts. A token anchor cannot separate "50 steps" from "step 50" —
#   both sit beside the word "steps" — so the counts fired on step indices and
#   the triage list was unusable. ANCHOR_PHRASES requires a phrase, in a 60-
#   character window rather than a 400-character one, with the number's own
#   value substituted into the phrase where it belongs.
#
# v1.5.0  # Hollingham (2026) — 2026-08-21. Integer-valued
#   quantities are searched at zero decimal places. The default precision set
#   is [2, 3, 4], so the step count was rendered "50.00" and matched nothing:
#   the manifest counts were registered, anchored and admitted, and still never
#   searched for. Whole numbers now get dp=0 added automatically.
#
# v1.4.0  # Hollingham (2026) — 2026-08-21. Adds the MIXED class,
#   which is where the corpus's real drift has been hiding. check_numbers()
#   stopped at the first document quoting a value correctly and called it
#   settled — so a number corrected in three documents and left stale in seven
#   reported as "cited and current". The scan now continues past that hit and
#   reports the stale occurrences as MIXED, sorted ahead of everything else: a
#   value that is right in one document and wrong in another is a sweep that
#   was started and not finished, which is more urgent than a value uniformly
#   out of date.
#
# v1.3.0  # Hollingham (2026) — 2026-08-21. The manifest counts
#   registered in v1.2.0 still did not fire, for two reasons found by probing
#   rather than by reading: the keys' anchors were the manifest's own field
#   names ("total", "registered") and not the words the documents use, and
#   searchable() rejects two-digit values outright, so "49" was never even
#   searched for. Keys are now named for the document vocabulary, and short
#   values are admitted for anchored manifest keys only. With both in place the
#   step count is found, anchored, in ten documents.
#
# v1.2.0  # Hollingham (2026) — 2026-08-21. Closes the two holes
#   that let stale numbers sit behind a clean gate.
#
#   (1) EVERY OCCURRENCE, not the indexed one. check_index() walks index ROWS,
#   and the index carries one row per (key, document). A value repeated across
#   documents was therefore checked in one of them: the clearfell step was
#   flagged in the Methods Supplement while the same stale figure stood in
#   report10 and in the Conclusions. sweep_repeats() now takes every stale
#   string the index check found and searches the WHOLE corpus for it, so a
#   number that appears in five documents is reported five times.
#
#   (2) THE MANIFEST COUNTS. A number with no key was never checked at all, and
#   the most-repeated numbers in the corpus - the registered step count, the
#   phase count, the tier and exec splits - had none. Registering Script 39
#   moved the step count from 49 to 50 and nine documents went stale in silence.
#   collect_values() now reads outputs/pipeline_manifest.json, so the counts
#   run_analysis.py already guards internally are guarded in the documents too.
#
# v1.1.0  # Hollingham (2026) — 2026-08-20. Matching is now
#        numeric-boundary aware and context aware, and the citation index's
#        stored `before`/`after` slices are finally used for what they were
#        recorded for. Every place that asked `needle in text` asked a
#        substring question and got a substring answer: 0.135 "found" inside
#        the frame height 10.135cm, 1.29 inside 11.298cm, 1.76 inside the
#        summer minimum -1.766 m, 30 inside "Figure 30" and inside "R2 <= 0.30",
#        15.45 inside width="15.45cm". Those matches drove both directions of
#        verdict - a phantom hit reported a value as "cited and current" when
#        no document quotes it, and a phantom near miss put a healthy value on
#        the triage list. `number_spans()` now yields only occurrences that are
#        whole numbers in a citable context, `quotes()` replaces the bare `in`
#        test, and `locate()` picks the occurrence an index row points at by
#        scoring the stored context against the document. No behaviour outside
#        matching changes: the anchor window, the near-miss span, the claims
#        rules and the exit codes are untouched.
#
# 1.0.0  marks the module's state before this change; it carried no
#        __version__ constant previously.

import argparse
import csv
import json
import re
import sys
from bisect import bisect_left, bisect_right
from collections import defaultdict
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]

# Mirrors, plus the documents that are already text. Never the ODTs. Keep in
# step with refresh_mirrors.py.
#
# "docs/**/text/*.md" replaces the two narrower docs globs so that adding a
# mirror directory to refresh_mirrors.py is enough - the corpus follows, and a
# document cannot be mirrored but unchecked.
#
# The repo's own markdown and index.html need no mirror: they are text already,
# and strip_markup() handles index.html's HTML. index.html is the only published
# page that states pipeline numbers, and only its step and phase counts were
# protected before 2026-08-18, via the PL markers.
DOC_GLOBS = [
    "report_edits/text/report*.md",
    "docs/**/text/*.md",
    "index.html",
    "readme.md",
    "PIPELINE_README.md",
    "REPORT_STRUCTURE.md",
    "DECISION_LOG.md",
    "ledgers/*.md",
]

# Paths the report sweeps must never read, whatever the globs above match.
#
# living/ is a separate operational lane (D-063): the Water Watch newsletter and
# the live forecaster feeds. Its hub, readings_living.csv, GROWS EVERY MONTH by
# design, while the report is fitted to a record that record_basis.csv declares.
# A sweep that read living/ would compare corpus numbers against a moving target
# and report drift that is not drift.
#
# It is excluded today only because no glob happens to reach it. That is not a
# guarantee — widening "docs/**/text/*.md" to "**/text/*.md" would pull it in
# silently — so the exclusion is stated here and enforced, rather than left to
# the accident of a pattern.
EXCLUDE_PREFIXES = ("living/",)


def _excluded(rel: str) -> bool:
    return any(rel.startswith(p) for p in EXCLUDE_PREFIXES)

# Headline tables whose values are cited directly rather than via a
# report-numbers key. (csv path, key column, value columns).
HEADLINE_TABLES = [
    ("outputs/03_state_space_model/03_03_cluster_mechanistic_coefficients.csv",
     "Cluster_Label",
     # Every column the mechanistic table renders, so the whole table is
     # covered rather than four of its six numeric columns.
     ["beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage",
      "R2", "LCSC_percent"]),
]

# Value tables that are NOT report-numbers files but whose numbers reach the
# documents. collect_values() reads outputs/**/*report_numbers*.csv, so a script
# that publishes into the prose without one is invisible to the whole check —
# not "not cited", never looked at. Script 15 was stale in four of five lambda
# values and four of five NSE improvements, and had flipped a published ranking,
# with the gate green throughout. Twenty-four output directories carry CSVs and
# no report-numbers file; these are the ones whose values are quoted.
#   (csv path, key column, value columns)  — same shape as HEADLINE_TABLES.
EXTRA_VALUE_TABLES = [
    ("outputs/15_depth_dependent_pet/15_04_best_params.csv", "Cluster",
     ["Best_Lambda", "NSE_Iterative", "SSM_NSE", "R2_OneStep"]),
    ("outputs/03_state_space_model/03_04_lag_diagnostic.csv", "Cluster_Label",
     ["R2"]),
    ("outputs/32_differential_movement/32_site_mean_trend.csv", "period",
     ["slope_mm_yr", "resid_sd_mm", "min_detectable_mm_yr"]),
    ("outputs/22_residual_lag_analysis/22_06_ssm_cluster_mean_inference.csv",
     "Cluster_Label", ["R2", "durbin_watson", "ar1_phi"]),
    ("outputs/39_ccw_hindcast/39_01_hindcast_per_well.csv", "well",
     ["nse", "pearson_r", "bias_m", "epoch_shift_m"]),
]

# Claims register. rule is evaluated against the named CSV.
#   argmin:<col>  / argmax:<col>  -> `expect` must be the value of `key_col`
# Extend this rather than restating a claim in prose.
CLAIMS_REGISTER = "tools/claims_register.csv"

# Exact citation index, built by tools/build_citation_index.py. Each row says
# "key K is quoted in document D as the literal string S". When the index has a
# row, the check is EXACT — no proximity guessing, no near-miss heuristic. The
# heuristic scan is then only for values the index does not yet cover.
CITATION_INDEX = "tools/citation_index.csv"

# Archived output trees produced by no live script — their values are history,
# not current publications, so they must not drive a staleness verdict.
EXCLUDE_OUTPUT_DIRS = ("30_c4_constrained_fit",)

# A rendering is searchable only if it carries enough significant digits to be
# distinctive. "0.02" matches thousands of unrelated places; "0.0183" does not.
MIN_SIG_DIGITS = 3

# Significant digits alone are not enough. In documents dense with per-well
# tables almost any 3-digit value collides with SOMETHING: the first triage run
# reported 14 hits above a 1% gap and all 14 were coincidences — a BACI spring
# shift "matched" the upper end of a cluster's beta_3 range, a p-value "matched"
# a seasonal amplitude in metres. A near miss is evidence only when it sits near
# a token identifying the quantity. Anchors are derived from the key.
ANCHOR_WINDOW = 400          # characters either side of the candidate number
_STOPWORDS = {
    "mean", "median", "shift", "after", "before", "step", "pct", "percent",
    "delta", "diff", "value", "total", "count", "min", "max", "range", "sum",
    "headline", "resid", "residual", "impact", "control", "ctrl", "model",
    "spring", "summer", "winter", "annual", "monthly", "per", "well", "wells",
    "cluster", "vs", "and", "the", "for", "with", "from", "test", "fit",
    "depth", "minimum", "maximum", "coeff", "intercept", "slope", "weight",
    # cluster-label words: they appear on every row of every per-well table
    "forest", "dune", "lake", "edge", "coastal", "residual", "western", "main",
    "warren", "reference", "extended", "calibration",
}


# Some keys need a PHRASE, not a token. The manifest counts are the case: they
# are small integers, and "49" sits near the word "steps" both when a document
# states the step COUNT and when it names step 49. A single-token anchor cannot
# tell those apart and floods the triage list with step indices. Where a key
# appears here, anchored() requires one of these phrases in the window instead
# of any derived token, and the phrase is matched with the number's own position
# so "50 steps" counts and "step 50" does not.
ANCHOR_PHRASES: dict[str, tuple[str, ...]] = {
    "pipeline_steps_registered": (
        "registered steps", "registered pipeline steps", "steps across",
        "steps in order", "-step", "step reproducible", "all {n} steps",
        "same {n} steps", "scripts ({n} steps", "total registered steps",
    ),
    "pipeline_phases_total": (
        "across {n} phases", "{n} phases", "phases 1-{n}", "phases 1--{n}",
    ),
    # These two need the NUMBER in the phrase. "analytical" and "default pass"
    # both sit beside step indices — "steps 36-41/50, all analytical-default" —
    # and a phrase that does not pin the number matches those too.
    "pipeline_steps_analytical": (
        "{n} analytical", "analytical top-level: {n}", "tier: {n}",
    ),
    "pipeline_steps_default": (
        "{n} in a default", "{n} run in a default", "execution: {n}",
        "default-exec {n}",
    ),
    "pipeline_steps_display": ("{n} display/utility",),
    "pipeline_steps_diagnostic": ("{n} diagnostic",),
    "pipeline_steps_optin": ("{n} opt-in", "{n} only under", "{n} only behind"),
}

PHRASE_WINDOW = 60           # characters either side, for phrase anchors


def phrase_anchored(text: str, needle: str, phrases) -> bool:
    """True if `needle` occurs with one of `phrases` close by.

    Deliberately tighter than anchored(): the window is a phrase's worth of
    characters, not a paragraph's, because the whole point is to separate a
    count from an index that sits near the same vocabulary.
    """
    low = text.lower()
    want = [ph.replace("{n}", needle).lower() for ph in phrases]
    for start, end in number_spans(text, needle):
        window = low[max(0, start - PHRASE_WINDOW): end + PHRASE_WINDOW]
        if any(w in window for w in want):
            return True
    return False


# A key often names BOTH a subject and a quantity — CoeffShift_CEH2_b1_before is
# well CEH2 and coefficient β₁. The subject alone is a weak anchor: report10 says
# "β₂ = 2.628 at NW10 is below CEH2 (β₂ = 2.891)", and a scan anchored on "CEH2"
# alone reads that 2.628 as a stale rendering of CEH2's β₁. Requiring a quantity
# marker too rejects it, because the quantity in that sentence is β₂.
#
# The coefficient shorthands never appear in prose in the form the CSV keys use,
# so the key's own token cannot do the work; this is the translation.
_QUANTITY_FORMS = {
    "b1": ["β₁", "beta_1", "beta 1", "recharge sensitivity"],
    "b2": ["β₂", "beta_2", "beta 2", "atmospheric draw"],
    "b3": ["β₃", "beta_3", "beta 3", "drainage coefficient", "drainage decay"],
    "r2": ["r²", "r2"],
    "sy": ["specific yield", "sy"],
    "nse": ["nse", "nash"],
    "se": ["standard error", "se"],
    "p": ["p ="],
}


def anchor_groups(key: str) -> tuple[list[str], list[str]]:
    """(subject anchors, quantity anchors) from a report-numbers key.

    Subjects are well and cluster ids — what the number is ABOUT. Quantities are
    the topic words and the coefficient shorthands — what the number IS. A key
    carrying both must match both, because a sentence naming the subject while
    reporting a different quantity is the commonest false positive in the sweep.
    """
    subj, quant = [], []
    for t in re.split(r"[_\W]+", key):
        if not t or t.lower() in _STOPWORDS:
            continue
        low = t.lower()
        if re.fullmatch(r"(?i)(ceh|nw|wmc|lis|fe|d|t)\d+[a-z]?", t):
            subj.append(t)                      # well id
        elif re.fullmatch(r"(?i)c[1-5]", t):
            subj.append(t)                      # cluster id
        elif low in _QUANTITY_FORMS:
            quant.extend(_QUANTITY_FORMS[low])
        elif t.isupper() and len(t) >= 3:
            quant.append(t)                     # acronym: BACI, ANCOVA, MSL...
        elif len(t) >= 5 and not t.isdigit():
            quant.append(t)                     # topic word
    return subj, quant


def anchors(key: str) -> list[str]:
    """Flat anchor list — kept for callers that do not need the split."""
    subj, quant = anchor_groups(key)
    return subj + quant


def anchored(text: str, needle: str, keys: list[str],
             key: str | None = None, strict: bool = False) -> bool:
    """True if `needle` occurs anywhere within ANCHOR_WINDOW of an anchor.

    A key listed in ANCHOR_PHRASES bypasses the token test entirely and must
    satisfy the tighter phrase test instead.

    `strict` demands a SUBJECT anchor and a QUANTITY anchor, not just either.
    The burden of proof scales with how speculative the claim is: finding the
    exact committed value near the well id is strong evidence the document is
    citing that number, so the exact-hit scan stays permissive. A NEAR MISS is
    weak evidence — it says "a different number sits near this well id" — and
    applied permissively it reports every other coefficient in the sentence.
    Demanding the quantity there costs nothing real and removes the commonest
    false positive in the triage list.
    """
    if key and key in ANCHOR_PHRASES:
        return phrase_anchored(text, needle, ANCHOR_PHRASES[key])
    if not keys:
        return True
    low = text.lower()
    subj, quant = anchor_groups(key) if key else ([], [])
    # When the key names both a subject and a quantity, demand both. When it
    # names only one, fall back to the flat any-match — tightening a key that
    # has nothing to tighten with only loses sensitivity.
    if strict and subj and quant:
        lowsubj = [k.lower() for k in subj]
        lowquant = [k.lower() for k in quant]
        for start, _end in number_spans(text, needle):
            window = low[max(0, start - ANCHOR_WINDOW): start + ANCHOR_WINDOW]
            if any(k in window for k in lowsubj) and any(k in window for k in lowquant):
                return True
        return False
    lowkeys = [k.lower() for k in keys]
    for start, _end in number_spans(text, needle):
        window = low[max(0, start - ANCHOR_WINDOW): start + ANCHOR_WINDOW]
        if any(k in window for k in lowkeys):
            return True
    return False


def _sig_digits(s: str) -> int:
    return len(re.sub(r"[^1-9]", "", s.lstrip("-0.").replace(".", "")) or "") + \
        len(re.findall(r"(?<=[1-9])0", s.replace(".", "")))


# Keys whose values are short whole numbers and would fail the significant-digit
# test, but which carry strong anchors ("pipeline", "steps", "phases") so a
# two-digit match near one of them is a citation rather than a coincidence. The
# manifest counts are the whole of this exception: they are the most-repeated
# numbers in the corpus and the general rule was hiding every one of them.
SHORT_VALUE_KEY_PREFIXES = ("pipeline_",)


def searchable(s: str, key: str | None = None) -> bool:
    digits = re.sub(r"[^0-9]", "", s).lstrip("0")
    if len(digits) >= MIN_SIG_DIGITS:
        return True
    if key and key.startswith(SHORT_VALUE_KEY_PREFIXES) and len(digits) >= 2:
        return True
    return False


# ---------------------------------------------------------------------------
# What counts as the corpus quoting a number
# ---------------------------------------------------------------------------
# `s in text` is a substring test, not a citation test, and a document is full
# of substrings that merely look like values. Three families account for
# nearly all of them:
#
#   EMBEDDED    the digits sit inside a longer number. 0.135 inside the frame
#               height 10.135cm; 1.29 inside 11.298cm; 1.76 inside the summer
#               minimum -1.766 m; 30 inside "R2 <= 0.30"; 3.30 inside 13.30.
#   GEOMETRY    the number is a page-layout dimension, not a measurement:
#               width="15.45cm", height="10.956cm". strip_markup() removes HTML
#               attributes but not the pandoc `{width=... height=...}` blocks
#               the mirrors are full of.
#   CROSS-REF   the number names a document part, not a quantity: "Figure 30",
#               "Figure 65", "Table 9".
#
# A phantom is not merely noise. It corrupts the verdict in BOTH directions: a
# phantom exact hit reports a value as "cited and current" when no document
# quotes it - masking a real omission - and a phantom near miss puts a healthy
# value on the triage list. Measured on the 2026-08-20 tree: 13 of 55 triage
# rows and 26 exact "cited and current" verdicts were substring artefacts, and
# 10 of the 59 locatable citation-index rows were being checked at a string
# that is not the citation.
#
# On signs: this corpus writes the Unicode minus U+2212 while render() emits an
# ASCII hyphen, and beta_2 is STORED positive but QUOTED negative (the design
# matrix negates PET). Sign agreement is therefore deliberately NOT required -
# a leading +, - or U+2212 is treated as a sign, so it neither breaks the
# numeric boundary nor has to match. What the boundary rule cares about is
# digits, not signs.

# Context immediately before the number that means it is not a citation.
_FRAME_ATTR = re.compile(r"(?i)(?:width|height)\s*[=:]\s*[\"']?$")
_XREF_LABEL = re.compile(
    r"(?i)\b(?:figure|fig|table|section|chapter|appendix|equation|eq|panel|"
    r"plate)s?\.?\s*$")
# Context immediately after: a typesetting unit glued to the digits. Units this
# project actually publishes in (m, mm, %, days) are never glued this way.
_TYPESET_UNIT = re.compile(r"(?i)^(?:cm|px|pt|em|ex)\b")

_CONTEXT_LOOKBEHIND = 40         # characters of preceding text the rules see


def _is_whole_number(text: str, start: int, end: int) -> bool:
    """True if text[start:end] is a complete number, not part of a longer one.

    Rejects a neighbouring digit on either side, a decimal point or thousands
    comma that itself has a digit beyond it (so "30" inside "0.30" and "234"
    inside "1,234" both fail), and a preceding ASCII letter, which is how a
    number glues to an identifier: "30" inside "CEH30", "3" inside "WMC3".
    """
    prev = text[start - 1] if start else ""
    nxt = text[end] if end < len(text) else ""
    if prev.isdigit() or nxt.isdigit():
        return False
    if prev in ".," and start >= 2 and text[start - 2].isdigit():
        return False
    if nxt in ".," and end + 1 < len(text) and text[end + 1].isdigit():
        return False
    if "a" <= prev.lower() <= "z":
        return False
    return True


def _citable_context(text: str, start: int, end: int) -> bool:
    """True unless the surrounding text says this number is not a quantity."""
    before = text[max(0, start - _CONTEXT_LOOKBEHIND):start]
    if _FRAME_ATTR.search(before) or _XREF_LABEL.search(before):
        return False
    if _TYPESET_UNIT.match(text[end:end + 6]):
        return False
    return True


def number_spans(text: str, needle: str):
    """Yield (start, end) for each occurrence of `needle` that is a whole
    number in a context where a number can be a citation."""
    for m in re.finditer(re.escape(needle), text):
        if _is_whole_number(text, m.start(), m.end()) and \
                _citable_context(text, m.start(), m.end()):
            yield m.start(), m.end()


def quotes(text: str, needle: str) -> bool:
    """True if the document quotes `needle` as a number. Use this, never
    `needle in text`."""
    return next(number_spans(text, needle), None) is not None


# Context relocation. build_citation_index.py stores CTX characters either side
# of each indexed citation, whitespace-normalised, precisely so the row can be
# re-found when a document has several renderings of the same string - and
# until now nothing read them except the DRIFTED printout. Scoring the stored
# slices against each candidate occurrence points the check at the citation the
# row is actually about.
_CONTEXT_SCAN = 120              # characters of document context compared


def _norm_ctx(s: str) -> str:
    """Normalise a context slice. Whitespace collapses (matching
    build_citation_index.norm) and backslashes are dropped: the mirrors gained
    pandoc escaping (`h\\_min`) after parts of the index were built, and the
    escape is not part of the text the citation sits in."""
    return " ".join(s.replace("\\", "").split()).lower()


def _common_tail(a: str, b: str) -> int:
    n = 0
    while n < min(len(a), len(b)) and a[-1 - n] == b[-1 - n]:
        n += 1
    return n


def _common_head(a: str, b: str) -> int:
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n]:
        n += 1
    return n


def _context_score(text: str, span: tuple[int, int], before: str,
                   after: str) -> int:
    """Characters of agreement between the stored context slices and the text
    actually surrounding `span`. Zero means the string is present but nowhere
    near where the index row recorded it."""
    s, e = span
    return (_common_tail(_norm_ctx(text[max(0, s - _CONTEXT_SCAN):s]),
                         _norm_ctx(before))
            + _common_head(_norm_ctx(text[e:e + _CONTEXT_SCAN]),
                           _norm_ctx(after)))


def locate(text: str, quoted: str, before: str = "",
           after: str = "") -> tuple[int, int] | None:
    """Span of the occurrence of `quoted` an index row points at, or None.

    With no stored context this is simply the first citable occurrence. With
    context it is the occurrence whose surroundings agree with the stored
    slices best. A poor best score is not grounds for rejection: prose gets
    rewritten around a number that is still cited, and the mirrors' escaping
    has changed since parts of the index were built.
    """
    spans = list(number_spans(text, quoted))
    if not spans:
        return None
    if not (before or after):
        return spans[0]
    return max(spans, key=lambda sp: _context_score(text, sp, before, after))


# An HTML tag: opens with a letter (element) or "!" (comment/doctype) and, in
# particular, contains NO further "<". That exclusion is load-bearing. The
# earlier pattern <[^>]+> matched from any "<" to the next ">" anywhere in the
# file, and the mirrors are full of bare less-than signs — every "p < 0.001" in
# a statistics table. One such "<" swallowed everything up to the next ">",
# which was typically hundreds of lines later, deleting whole tables of cited
# values before the checker ever saw them: report9 stripped from 267 kB to
# 97 kB, and 117 indexed citations were reported MOVED when the numbers were
# sitting in the document all along. Silent blindness, not noise — a drifted
# value inside a swallowed table could never have been caught. See D-018.
_MARKUP = re.compile(r"</?[A-Za-z!][^<>]*>")
_IMGREF = re.compile(r"!?\[[^\]]*\]\([^)]*\)")   # markdown links / images


def strip_markup(text: str) -> str:
    """Remove markup so only prose and table CONTENT is searched.

    The mirrors carry raw HTML for figures and tables. Without this, a CSS
    dimension (style="height:10.118cm") or an image filename is a searchable
    number, and every one of them is a false positive waiting to happen.
    """
    return _IMGREF.sub(" ", _MARKUP.sub(" ", text))


def load_documents() -> dict[str, str]:
    docs: dict[str, str] = {}
    for g in DOC_GLOBS:
        for p in REPO.glob(g):
            if _excluded(str(p.relative_to(REPO))):
                continue
            try:
                docs[str(p.relative_to(REPO))] = strip_markup(
                    p.read_text(encoding="utf8"))
            except OSError:
                pass
    return docs


def render(v: float, dp: int) -> str:
    return f"{v:.{dp}f}"


def near_misses(v: float, dp: int, span: int) -> list[str]:
    """Renderings within `span` units of the last decimal place, excluding v.

    "Excluding v" has to mean excluding v's own RENDERING, not merely skipping
    k = 0. Binary floating point breaks the two apart: 2.0865 renders at three
    decimals as "2.087", and so does 2.0865 + 0.001, because that sum is really
    2.08749999999999991. So the correct rendering was being generated as a near
    miss of itself, and every document quoting the number correctly was reported
    as drifted. That accounted for most of a 200-row triage list, all of it
    under a 1 % gap, and it is why the list had stopped being read.
    """
    step = 10 ** -dp
    self_render = render(v, dp)
    out = []
    for k in range(-span, span + 1):
        if k == 0:
            continue
        r = render(v + k * step, dp)
        if r != self_render and r not in out:
            out.append(r)
    return out


def collect_values() -> list[tuple[str, str, float]]:
    """[(source, label, value)] from report-numbers files and headline tables."""
    vals: list[tuple[str, str, float]] = []
    for p in sorted(REPO.glob("outputs/**/*report_numbers*.csv")):
        if any(d in p.parts for d in EXCLUDE_OUTPUT_DIRS):
            continue
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        cols = {c.lower(): c for c in df.columns}
        kcol = cols.get("key") or df.columns[0]
        vcol = cols.get("value")
        if vcol is None:
            num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if not num:
                continue
            vcol = num[0]
        for _, r in df.iterrows():
            try:
                vals.append((str(p.relative_to(REPO)), str(r[kcol]), float(r[vcol])))
            except (TypeError, ValueError):
                continue
    # Manifest counts. These are the most-repeated numbers in the corpus and
    # had no key, so nothing checked them: run_analysis.py guards its own
    # _DOCUMENTED_COUNTS internally, but that guard never reached the prose.
    # Sourced from the committed manifest so the documents are checked against
    # what the pipeline actually registered, not against a second declaration.
    man = REPO / "outputs" / "pipeline_manifest.json"
    if man.exists():
        try:
            m = json.loads(man.read_text(encoding="utf8"))
            flat = {k: v for k, v in m.items() if isinstance(v, (int, float))}
            for grp in ("by_tier", "by_exec"):
                for k, v in (m.get(grp) or {}).items():
                    if isinstance(v, (int, float)):
                        flat[f"{grp}.{k}"] = v
            # Key names are chosen so anchors() derives the words the
            # DOCUMENTS use — "pipeline", "steps", "phases" — rather than the
            # manifest's own field names. A near miss is only reported when it
            # sits near an anchor, so "49 steps across 17 phases" is invisible
            # to a key anchored on "registered" and "total".
            rename = {
                "total_registered":            "pipeline_steps_registered",
                "total_phases":                "pipeline_phases_total",
                "analytical_phases":           "pipeline_phases_analytical",
                "scraping_substeps":           "pipeline_scraping_substeps",
                "clearfell_substeps":          "pipeline_clearfell_substeps",
                "by_tier.analytical_toplevel": "pipeline_steps_analytical",
                "by_tier.display_utility":     "pipeline_steps_display",
                "by_tier.optin_diagnostic":    "pipeline_steps_diagnostic",
                "by_exec.default":             "pipeline_steps_default",
                "by_exec.optin":               "pipeline_steps_optin",
            }
            for k, v in flat.items():
                name = rename.get(k, f"pipeline_{k}")
                # Only counts with a phrase anchor are registered. A small
                # integer without one cannot be told from a step index and
                # would report every occurrence of "13" in the corpus. Two are
                # deliberately absent: analytical_phases, which the working
                # rules say is emitted for completeness and cited nowhere, and
                # the sub-step counts, which appear only as ranges.
                if name not in ANCHOR_PHRASES:
                    continue
                vals.append(("outputs/pipeline_manifest.json", name, float(v)))
        except (OSError, ValueError):
            pass

    for rel, kcol, vcols in list(HEADLINE_TABLES) + list(EXTRA_VALUE_TABLES):
        p = REPO / rel
        if not p.exists():
            continue
        df = pd.read_csv(p)
        for _, r in df.iterrows():
            for c in vcols:
                try:
                    vals.append((rel, f"{r[kcol]} · {c}", float(r[c])))
                except (TypeError, ValueError, KeyError):
                    continue
    return vals


# ---------------------------------------------------------------------------
# SPREAD — one quantity, several renderings
# ---------------------------------------------------------------------------
# Every other check in this file asks "does the corpus quote the committed
# value?". That question has a blind spot: a quantity the documents deliberately
# round — a modelled reach stated to the nearest tens of metres, say — never
# equals the CSV at any searched precision, so it lands in the uncited bin and
# no check ever looks at it again. Meanwhile the documents are free to disagree
# with each other, and they do.
#
# SPREAD asks the other question: does the corpus quote the SAME value
# everywhere? It collects every rendering that sits near the quantity's anchor
# and reports the distinct set. More than one member is the finding.
#
# Each register entry is (anchor phrases, window, relative band, exclusions):
#   anchors     one must appear within `window` characters of the number. For a
#               quantity with a symbol, the symbol is the anchor — it is far
#               tighter than the key's own vocabulary.
#   window      characters either side. Deliberately small; a paragraph-sized
#               window sweeps in every other number in the paragraph.
#   band        renderings are kept only within this relative distance of the
#               committed value, so an unrelated number near the same symbol is
#               not mistaken for a rendering of this quantity.
#   exclusions  a phrase in the window that means this occurrence is a DIFFERENT
#               quantity sharing the symbol. λ names both the drawdown reach and
#               the scraping covariate; the register is where they are separated,
#               and tools/symbol_register.csv carries the same distinction for
#               the symbol audit.
LARGE_VALUE_MIN = 100.0

# Documents whose job is to record what a value USED to be. A spread check on
# them reports the history as though it were disagreement, which inverts their
# purpose: the Decision Log and the ledgers are where a superseded number is
# supposed to survive. They stay inside every other check.
SPREAD_EXCLUDE_DOCS = ("DECISION_LOG.md", "NUMBER_LEDGER.md",
                       "SCRIPT_LEDGER.md", "FIGURE_LEDGER.md")

QUANTITY_ANCHORS = {
    # The forest/scrape reach. λ also names the scraping BACI covariate and the
    # P_flood rainfall multiplier, so the exclusions carry the same sense
    # separation that tools/symbol_register.csv carries for the symbol audit.
    "drawdown_lambda": (["λ"], 40, 0.15,
                        ["scraping", "covariate", "spans roughly", "sensitivity",
                         "500 m", "p_flood", "p\\_flood", "multiplier"]),
    # The coastal fit's parameters, quoted rounded in six passages across three
    # chapters and previously drifted by a whole generation of the fit (D-047,
    # D-039). δ₀ is the shoreline amplitude, not the headline; the headline is
    # quoted at the reference distance and is registered separately.
    "Headline_fit_delta_0": (["δ₀"], 45, 0.12,
                             ["150 m", "reference distance", "95 % ci", "95% ci"]),
    "Headline_coastal_rate_at_ref": (["coast-edge trend", "at the 150 m",
                                      "reference distance"], 90, 0.12, []),
    "Headline_fit_L": (["reach", "strip-aquifer width", "inland over"], 45, 0.10,
                       # 2√(Dt) is the diffusive length-scale of the sea-level-rise
                       # field, and a cluster's mean distance to the coast is a
                       # position, not the reach. Both sit next to the word "reach".
                       ["scraping", "λ", "√(dt)", "mean distance", "roughly 900",
                        "about 900", "≈ 900"]),
}

# A leading minus is only a minus when nothing precedes it. In the pandoc
# mirrors an en dash is written "--", so "16--17" was yielding "-17" as a
# negative number and the phase count appeared to disagree with itself.
_NUMERIC = re.compile(r"(?<![\w.\-–—])(-?\d+(?:\.\d+)?)(?![\w.])")


_NUM_INDEX: list | None = None       # [(abs_value, doc, rendering, start, end)]
_NUM_KEYS: list | None = None        # the magnitudes alone, for bisect


def _number_index(docs) -> list:
    """Every numeric token in the corpus, once, sorted by magnitude.

    --spread-all asks the same question of a thousand values. Rescanning the
    corpus per value is a thousand passes; indexing once and bisecting into the
    band is one. Built lazily so the default run pays nothing extra.
    """
    global _NUM_INDEX, _NUM_KEYS
    if _NUM_INDEX is None:
        idx = []
        for doc, text in sorted(docs.items()):
            if doc.split("/")[-1] in SPREAD_EXCLUDE_DOCS:
                continue
            for m in _NUMERIC.finditer(text):
                try:
                    x = abs(float(m.group(1)))
                except ValueError:
                    continue
                idx.append((x, doc, m.group(1), m.start(), m.end()))
        idx.sort(key=lambda r: r[0])
        _NUM_INDEX = idx
        _NUM_KEYS = [r[0] for r in idx]
    return _NUM_INDEX


def renderings_near(docs, value, anchor_list, window, band, excludes,
                    require_all=False):
    """{rendering: [documents]} for every number near an anchor and in band."""
    idx = _number_index(docs)
    keys = _NUM_KEYS
    lo, hi = abs(value) * (1 - band), abs(value) * (1 + band)
    out: dict[str, list[str]] = defaultdict(list)
    lowanchors = [a.lower() for a in anchor_list]
    lowex = [e.lower() for e in excludes]
    for x, doc, rendering, start, end in idx[bisect_left(keys, lo):
                                             bisect_right(keys, hi)]:
        text = docs[doc]
        win = text[max(0, start - window): end + window].lower()
        ok = (all(a in win for a in lowanchors) if require_all
              else any(a in win for a in lowanchors))
        if not ok:
            continue
        if any(e in win for e in lowex):
            continue
        out[rendering].append(doc)
    return out


def generic_anchors(key: str):
    """Fallback register entry for --spread-all: the key's own vocabulary.

    Far stricter than a registered entry, and it has to be. A registered entry
    anchors on the quantity's own symbol, which is unambiguous; a key's tokens
    are words like "C3" and "NSE" that sit near dozens of unrelated numbers. So
    the fallback demands EVERY token inside a tight window and a 2 % band, and
    even then this mode is a way of finding quantities that DESERVE a register
    entry, not a findings list. Anything it surfaces should be read, checked by
    hand, and then registered properly with its own anchor.
    """
    toks = anchors(key)
    if len(toks) < 2:
        return None
    return (toks, 60, 0.02, [], True)


def check_spread(docs, values, spread_all=False, gate=False) -> int:
    print("=" * 78)
    print("SPREAD — does the corpus quote the same value everywhere?")
    print("=" * 78)
    print("  A quantity the documents round never matches the CSV at any searched"
          "\n  precision, so the other checks cannot see it disagree with itself."
          "\n  More than one rendering near the same anchor is the finding.")
    seen, hits = set(), 0
    for source, label, v in values:
        if not (abs(v) > 0) or (label, v) in seen:
            continue
        seen.add((label, v))
        entry = QUANTITY_ANCHORS.get(label)
        if entry is None:
            if not spread_all:
                continue
            entry = generic_anchors(label)
            if entry is None:
                continue
        found = renderings_near(docs, v, *entry)
        if len(found) <= 1:
            continue
        hits += 1
        print(f"\n  {label}   committed {v:g}   ({source})")
        for r, where in sorted(found.items(), key=lambda kv: -len(kv[1])):
            docs_ = sorted({d.split("/")[-1] for d in where})
            print(f"      {r:>10s}  x{len(where):<3d} {', '.join(docs_)}")
    if not hits:
        print("\n  No registered quantity is rendered inconsistently.")
    else:
        print(f"\n  {hits} quantity(ies) rendered inconsistently across the corpus.")
        if not gate:
            print("  Advisory — pass --spread-gate to make this a gating check.")
    return hits if gate else 0


def check_numbers(docs, dps, span, min_rel=0.0, csv_out=None) -> int:
    print("=" * 78)
    print("NUMBERS — every published value vs the corpus")
    print("=" * 78)
    stale, uncited, ok = [], [], 0
    seen: set[tuple[str, float]] = set()
    for source, label, v in collect_values():
        if not (abs(v) > 0):
            continue
        # 10_consolidated_report_numbers.csv republishes the per-script 10x
        # values verbatim; counting both inflates the hit list without adding
        # a single new place to check.
        if (label, v) in seen:
            continue
        seen.add((label, v))
        hit_dp = None
        anc = anchors(label)
        # Whole numbers are written without a decimal point, and the default
        # precision set starts at two: rendering the step count as "50.00" finds
        # nothing, and the count was never searched for at all. Any integer-
        # valued published quantity has the same problem.
        # Whole numbers, and any quantity of order hundreds or more, are
        # written without a decimal point in prose. Rendering a 226 m reach as
        # "226.44" finds nothing, and the quantity is then reported as uncited
        # rather than as quoted-and-rounded.
        dps_v = list(dps)
        if float(v).is_integer() or abs(v) >= LARGE_VALUE_MIN:
            dps_v = [0] + dps_v
        for dp in dps_v:
            s = render(v, dp)
            if not searchable(s, label):
                continue
            if any(quotes(t, s) and anchored(t, s, anc, label)
                   for t in docs.values()):
                hit_dp = dp
                break
        # A value found SOMEWHERE was previously treated as settled, and the
        # scan stopped. That is the deepest form of the repeats problem: a
        # number corrected in three documents and left stale in seven reads as
        # "cited and current", because one hit satisfied the check. The scan now
        # continues in both cases; when the current value is present the stale
        # occurrences are reported as MIXED, which is a different and more
        # urgent finding than a value that is wrong everywhere.
        mixed = hit_dp is not None
        if mixed:
            ok += 1
        found = []
        for dp in sorted(dps_v, reverse=True):   # most precise first
            if not searchable(render(v, dp), label):
                continue
            anc = anchors(label)
            for nm in near_misses(v, dp, span):
                if not searchable(nm, label):
                    continue
                where = [d for d, t in docs.items()
                         if quotes(t, nm)
                         and anchored(t, nm, anc, label, strict=True)]
                if where:
                    found.append((nm, dp, where))
            if found:
                break                          # one precision level is enough
        if found:
            gaps = [abs(float(nm) - v) / abs(v) for nm, _, _ in found]
            rel = min(gaps) if gaps else 0.0
            if rel >= min_rel:
                stale.append((source, label, v, found, rel, mixed))
        elif not mixed:
            uncited.append((source, label, v))

    # MIXED first: a value that is right in one document and wrong in another
    # is the more urgent class, whatever the size of the gap.
    stale.sort(key=lambda r: (not r[5], -r[4]))

    if csv_out:
        import csv as _csv
        with open(csv_out, "w", newline="", encoding="utf8") as fh:
            w = _csv.writer(fh)
            w.writerow(["rel_gap_pct", "key", "committed", "corpus_value",
                        "documents", "source_csv", "class"])
            for source, label, v, found, rel, mixed in stale:
                nm, _dp, where = found[0]
                w.writerow([f"{rel*100:.2f}", label, f"{v:g}", nm,
                            "; ".join(sorted(where)), source,
                            "MIXED" if mixed else "STALE"])
        print(f"  triage list written to {csv_out}")
    else:
        for source, label, v, found, rel, mixed in stale:
            tag = "MIXED " if mixed else "STALE?"
            note = ("  — the current value IS quoted elsewhere, so these "
                    "documents were missed by an earlier sweep" if mixed else "")
            print(f"\n  {tag}  {label}   (gap {rel*100:.2f}%){note}")
            print(f"          committed {v:g}   ({source})")
            for nm, dp, where in found[:3]:
                print(f"          corpus has {nm} at {dp}dp in: "
                      f"{', '.join(sorted(where))}")

    print(f"\n  {ok} value(s) cited and current; {len(stale)} possible stale "
          f"citation(s){f' above {min_rel*100:g}%' if min_rel else ''}; "
          f"{len(uncited)} not cited anywhere (informational).")
    return len(stale)


def check_index(docs, values) -> int:
    """Exact verification of every indexed citation.

    Three outcomes per row, and the distinction matters:
      OK       the document still quotes the current value.
      DRIFTED  the document still contains the indexed string, but the pipeline
               value has moved — the citation is now stale. This is the failure
               the whole exercise exists to catch, and it is exact: no
               proximity, no rounding guess.
      MOVED    the indexed string is gone from the document. Usually the prose
               was rewritten. Not an error, but the index row needs re-pointing
               or the citation has been dropped.
    """
    idx = REPO / CITATION_INDEX
    print()
    print("=" * 78)
    print("CITATIONS — exact check of the citation index")
    print("=" * 78)
    if not idx.exists():
        print(f"  no index at {CITATION_INDEX} — run "
              "tools/build_citation_index.py")
        return 0

    current = {}
    for _src, label, v in values:
        current.setdefault(label, v)

    ok = drifted = moved = unknown = advisory = 0
    # (key, stale string, current string, document the index row named). Filled
    # as rows are checked and swept across the whole corpus afterwards, because
    # the index carries one row per document and a repeated number is otherwise
    # checked in one place only.
    stale_strings: list[tuple[str, str, str, str]] = []
    for row in csv.DictReader(open(idx, encoding="utf8")):
        # Rejected rows are recorded coincidences — keeping them stops the
        # builder re-proposing them, but they are not citations to check.
        if row.get("status") == "rejected":
            continue
        key, doc, quoted = row["key"], row["document"], row["quoted"]
        text = docs.get(doc)
        if text is None:
            continue
        if key not in current:
            unknown += 1
            continue
        dp = len(quoted.split(".")[1]) if "." in quoted else 0
        want = render(current[key], dp)
        # Compare NUMBERS, not glyphs. Two of the drifted rows were never drift:
        # report9 quotes "−0.03" with U+2212 against a rendered "-0.03", and
        # "+0.82" with an explicit plus against a rendered "0.82". Both are the
        # same value written differently, and reporting them as stale citations
        # is how a gating check teaches its reader to ignore it.
        def _same(a: str, b: str) -> bool:
            f = lambda x: x.replace("\u2212", "-").lstrip("+")
            return f(a) == f(b)
        # The row's own before/after slices pick which occurrence it means.
        span = locate(text, quoted, row.get("before", ""), row.get("after", ""))
        present = span is not None
        if present and _same(want, quoted):
            ok += 1
        elif present:
            if row.get("status") == "confirmed":
                drifted += 1
            else:
                advisory += 1
            print(f"\n  DRIFTED  {key}  [{row.get('status','')}]")
            print(f"           {doc} quotes {quoted}, pipeline now says {want}")
            stale_strings.append((key, quoted, want, doc))
            # Context as the DOCUMENT now reads at the located occurrence,
            # not as the index recorded it: the point is to show where the
            # stale string still sits.
            s, e = span
            # A score of 0 means the string is present but not where the index
            # says: the located occurrence may be a coincidence rather than
            # the citation, and the row wants re-pointing before it is trusted.
            agree = _context_score(text, span, row.get("before", ""),
                                   row.get("after", ""))
            print(f"           ...{_norm_ctx(text[max(0, s - 50):s])} "
                  f"[{quoted}] {_norm_ctx(text[e:e + 50])}...")
            if not agree:
                print("           (stored context does not match here — "
                      "location unconfirmed, re-point the index row)")
        else:
            moved += 1
            if quotes(text, want):
                ok += 0   # value updated in prose but index not re-pointed
                print(f"\n  REPOINT  {key}: {doc} now quotes {want} "
                      f"(index still says {quoted}) — update the index row")
                # The indexed document has been updated; other documents may
                # still carry the old string, and nothing else would look.
                stale_strings.append((key, quoted, want, doc))
            else:
                print(f"\n  MOVED    {key}: {quoted} no longer in {doc} "
                      "— prose rewritten, or citation dropped")
    sweep_repeats(docs, stale_strings)
    print(f"\n  {ok} citation(s) exact and current; {drifted} DRIFTED "
          f"(confirmed rows — these gate); {advisory} drifted on unreviewed "
          f"rows (advisory); {moved} moved/re-pointed; "
          f"{unknown} key(s) no longer published.")
    return drifted


def sweep_repeats(docs, stale_strings) -> None:
    """Search the whole corpus for every stale string the index check found.

    The index holds one row per (key, document), so a value quoted in five
    documents is verified in one of them and the other four stand unexamined
    behind a passing gate. This takes each stale string the index check
    identified and looks for it everywhere else, in a citable context, so the
    repeats surface with the original.

    Reported separately from DRIFTED because these locations have no index row:
    they are places to check and re-point, not rows that already gate.
    """
    if not stale_strings:
        return
    seen: set[tuple[str, str]] = set()
    hits: list[tuple[str, str, str, str]] = []
    for key, quoted, want, indexed_doc in stale_strings:
        for doc, text in docs.items():
            if doc == indexed_doc or (doc, quoted) in seen:
                continue
            if not quotes(text, quoted):
                continue
            seen.add((doc, quoted))
            hits.append((key, quoted, want, doc))
    if not hits:
        return
    print()
    print("-" * 78)
    print("REPEATS — the same stale string in documents the index does not cover")
    print("-" * 78)
    for key, quoted, want, doc in sorted(hits, key=lambda h: (h[0], h[3])):
        print(f"  UNINDEXED  {key}: {doc} also carries {quoted} "
              f"(pipeline says {want}) — no index row covers this occurrence")
    docs_hit = len({h[3] for h in hits})
    print(f"\n  {len(hits)} unindexed occurrence(s) across {docs_hit} document(s). "
          "Each needs the same edit as its indexed twin, and an index row so it "
          "is checked next time.")


def check_claims(docs) -> int:
    reg = REPO / CLAIMS_REGISTER
    print()
    print("=" * 78)
    print("CLAIMS — assertions with no number, checked against the CSV")
    print("BREACH = the CSV says the claim is false AND a document asserts it")
    print("=" * 78)
    if not reg.exists():
        print(f"  no register at {CLAIMS_REGISTER} — skipped")
        return 0
    bad = 0
    for row in csv.DictReader(open(reg, encoding="utf8")):
        p = REPO / row["csv"]
        if not p.exists():
            print(f"  SKIP   {row['claim_id']}: {row['csv']} missing")
            continue
        df = pd.read_csv(p)
        kind, _, col = row["rule"].partition(":")
        if kind not in {"argmin", "argmax"} or col not in df.columns:
            print(f"  SKIP   {row['claim_id']}: unsupported rule {row['rule']!r}")
            continue
        idx = df[col].idxmin() if kind == "argmin" else df[col].idxmax()
        actual = str(df.loc[idx, row["key_col"]])
        holds = actual == row["expect"]

        needle = row.get("phrase", "").strip()
        where = [d for d, t in docs.items() if needle in t] if needle else []

        # Gate on ASSERTED-AND-FALSE, not on false alone. Entries kept as
        # tripwires are false by design — that is the point of keeping them.
        asserted_false = (not holds) and bool(where)
        if asserted_false:
            bad += 1

        verdict = "BREACH" if asserted_false else ("HOLDS " if holds else "false ")
        did = (row.get("decision_id") or "").strip()
        print(f"  {verdict} {row['claim_id']}"
              f"{f' [{did}]' if did else ''}: {row['assertion']}")
        if not holds:
            print(f"          {row['rule']} is {actual!r}, not {row['expect']!r}")
        if where:
            print(f"          asserted in: {', '.join(sorted(where))}")
        elif not holds:
            print("          not asserted in the corpus — tripwire only")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dp", nargs="+", type=int, default=[2, 3, 4])
    ap.add_argument("--near", type=int, default=2,
                    help="near-miss span in units of the last decimal place")
    ap.add_argument("--claims-only", action="store_true")
    ap.add_argument("--index-only", action="store_true",
                    help="exact citation-index check only; skip the heuristic "
                         "near-miss scan")
    ap.add_argument("--min-rel", type=float, default=0.0,
                    help="only report hits whose relative gap exceeds this "
                         "(e.g. 0.005 hides rounding-level differences)")
    ap.add_argument("--csv", default=None,
                    help="write the triage list to a CSV and print a summary only")
    ap.add_argument("--spread-all", action="store_true",
                    help="run the SPREAD check over every published value using "
                         "the key's own vocabulary as the anchor, not just the "
                         "quantities in QUANTITY_ANCHORS. Exploratory: noisier, "
                         "and it is how a quantity earns a register entry.")
    ap.add_argument("--spread-gate", action="store_true",
                    help="make SPREAD a gating check rather than advisory")
    args = ap.parse_args()

    docs = load_documents()
    if not docs:
        print("No mirrors found — run tools/refresh_mirrors.py first.")
        return 1
    print(f"corpus: {len(docs)} mirror(s)\n")

    rc = 0
    if not args.claims_only:
        values = collect_values()
        rc += check_index(docs, values)
        if not args.index_only:
            rc += check_numbers(docs, args.dp, args.near, args.min_rel, args.csv)
            rc += check_spread(docs, values, args.spread_all, args.spread_gate)
    rc += check_claims(docs)
    return 1 if rc else 0


if __name__ == "__main__":
    sys.exit(main())
