#!/usr/bin/env python3
"""
number_index.py
===============
An index of every named pipeline number and every place the corpus quotes it.

WHY
    `cite_check`'s NUMBERS section already gathers the committed values and
    already matches them against the mirrors. It then PRINTS the result and
    throws it away. Nothing can sort it, group it, or diff it against the last
    run. This tool persists what that machinery computes, as one row per
    (committed value, document, occurrence), so the three questions in
    working/updates/NRG_spec_number_index_2026-09-02.md can be asked of a file:

      1. what is furthest wrong?          -> sort by |gap_pct|
      2. is a citation cluster consistent? -> group by (document, source_csv)
      3. what changed since last time?     -> diff two emitted CSVs

WHAT IT IS NOT
    IT DOES NOT GATE. It emits `outputs/number_index.csv` and exits 0, always.
    It is deliberately absent from tools/check_all.sh. The noise level of a
    wide-band scan is unmeasured, and cite_check's own history is the argument:
    v1.10.0 records a 200-row triage list, nearly all under a 1 % gap, that
    "had stopped being read". Measure first, threshold later.

HOW IT DIFFERS FROM THE GATE
    cite_check searches a NEAR-MISS WINDOW of +/-`--near` units of the last
    decimal place. That window is narrow by design, because every candidate it
    admits is a candidate for the triage list. The three errors found by hand
    on 2026-09-02 sat at 11 %, 16 % and 4 % and were all outside it: at four
    decimal places a +/-2-unit window around 0.0241 reaches 0.0243, not 0.028.

    So this tool searches a RELATIVE BAND (`--band`, default 25 %) instead, and
    it searches it the cheap way round: rather than generating candidate
    renderings per value, it indexes every citable numeric token in the corpus
    once and bisects into the band. 7,759 searchable tokens across 38 mirrors,
    built in about 0.2 s.

    Everything else is cite_check's, imported and called, not restated:
    `collect_values`, `load_documents`, `render`, `anchors`, `anchored`,
    `searchable`, `_is_whole_number`, `_citable_context`, and the M31
    millimetre rules. The matching is not reimplemented; only the persistence
    and the band are new.

COLUMNS
    key         the named quantity, as collect_values() labels it
    source_csv  where it is committed
    committed   the value as stored, signed
    document    the mirror quoting it
    quoted      the rendering found in the document, unsigned
    dp          decimal places of that rendering
    gap_pct     100*(|quoted| - |committed|)/|committed|, signed
    unit_shift  blank, or `m->mm` where the metre/millimetre rule applied
    context     +/-70 characters around the occurrence, whitespace-normalised

CAVEATS A READER MUST CARRY
  * MAGNITUDES, NOT SIGNS. cite_check deliberately does not require sign
    agreement (the corpus writes U+2212, beta_2 is stored positive and quoted
    negative). `gap_pct` is therefore computed on absolute values. A sign flip
    is invisible here, as it is to the gate.
  * ASYMMETRIC ANCHORING, inherited from check_numbers: a rendering that IS the
    committed value correctly rounded is accepted on a permissive anchor, and
    anything else must satisfy the strict subject-AND-quantity anchor. That is
    the right burden of proof for a gate, but it means the near-zero end of the
    gap distribution is sampled more generously than the tail. `--strict-all`
    applies the strict test everywhere, for measuring that effect.
  * `searchable()` (>= 3 significant digits) suppresses low-precision
    renderings, so a committed 0.0241 quoted as "0.024" is NOT indexed. The
    rounding-noise end of the distribution is truncated for small-magnitude
    values, and the emitted distribution understates it.
  * Values are de-duplicated on (key, value) exactly as check_numbers does, so
    a value republished verbatim by 10_consolidated_report_numbers.csv is
    attributed to one source_csv, not two.

Version 1.0.0 -- Hollingham (2026), 2026-09-02.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from bisect import bisect_left, bisect_right
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cite_check as cc                                   # noqa: E402

__version__ = "1.0.0"

REPO = cc.REPO
OUT = REPO / "outputs" / "number_index.csv"

CTX = 70                     # characters of context either side, as
                             # tools/citation_index.csv stores (it splits them
                             # into before/after; the spec asks for one field)

FIELDS = ["key", "source_csv", "committed", "document", "quoted", "dp",
          "gap_pct", "unit_shift", "context"]

_WS = re.compile(r"\s+")


def norm_ctx(s: str) -> str:
    return _WS.sub(" ", s.replace("\\", "")).strip()


def token_index(docs: dict[str, str]) -> tuple[list, list]:
    """[(magnitude, doc, rendering, start, end)] sorted by magnitude.

    Every numeric token in the corpus that cite_check would accept as a
    citation: a whole number (`_is_whole_number`), in a citable context
    (`_citable_context`, which is what rejects `width="15.45cm"` and
    "Figure 30"), carrying enough significant digits to be distinctive
    (`searchable`).

    WHY THIS IS NOT cite_check._number_index(). That function exists and does
    almost this, but it (a) drops the match offsets, so no context or
    per-occurrence anchoring is possible, and (b) hard-codes the SPREAD check's
    exclusion of the Decision Log and the ledgers, which belong in this index.
    Both would be a two-line signature change there; the brief for this tool
    forbids touching cite_check, so the loop is rebuilt here out of cite_check's
    own imported predicates rather than its own rules.
    """
    idx = []
    for doc, text in sorted(docs.items()):
        for m in cc._NUMERIC.finditer(text):
            rend = m.group(1)
            start, end = m.start(1), m.end(1)
            if rend.startswith("-"):        # index unsigned: cite_check does
                rend, start = rend[1:], start + 1   # not require sign agreement
            # KEY-AGNOSTIC AT INDEX TIME, KEY-AWARE AT LOOKUP. cite_check's
            # searchable() takes an optional key, because the manifest counts
            # are two-digit numbers admitted by SHORT_VALUE_KEY_PREFIXES that
            # the general 3-significant-digit rule would drop. An index built
            # once for every key cannot apply a per-key exception, so it keeps
            # anything with two digits and searchable(rend, key) is applied at
            # lookup instead. Built with the 3-digit rule, this index held no
            # row for any pipeline_* key at all -- and the largest gaps in the
            # corpus on 2026-09-02 were three PIPELINE_README step counts.
            if len(re.sub(r"[^0-9]", "", rend).lstrip("0")) < 2:
                continue
            if not cc._is_whole_number(text, start, end):
                continue
            if not cc._citable_context(text, start, end):
                continue
            try:
                idx.append((abs(float(rend)), doc, rend, start, end))
            except ValueError:
                continue
    idx.sort(key=lambda r: r[0])
    return idx, [r[0] for r in idx]


_SEARCHABLE: dict[tuple[str, bool], bool] = {}


def searchable_for(rend: str, key: str) -> bool:
    """cite_check.searchable(), memoised.

    Called once per token per band slice -- millions of times over a full run --
    and it does a regex substitution per call. The answer depends only on the
    rendering and on whether the key is one of SHORT_VALUE_KEY_PREFIXES, so the
    cache is exact rather than an approximation of the rule.
    """
    short = key.startswith(cc.SHORT_VALUE_KEY_PREFIXES)
    ck = (rend, short)
    hit = _SEARCHABLE.get(ck)
    if hit is None:
        hit = _SEARCHABLE[ck] = cc.searchable(rend, key if short else None)
    return hit


def in_band(idx, keys, centre: float, band: float):
    lo, hi = abs(centre) * (1.0 - band), abs(centre) * (1.0 + band)
    return idx[bisect_left(keys, lo):bisect_right(keys, hi)]


def decimals(rend: str) -> int:
    return len(rend.split(".")[1]) if "." in rend else 0


def is_rounding_of(v: float, rend: str) -> bool:
    """True if `rend` is the committed value correctly rendered at its own dp."""
    return cc.render(abs(v), decimals(rend)) == rend


def anchored_here(text: str, start: int, end: int, rend: str,
                  anc: list, key: str, strict: bool) -> bool:
    """cite_check.anchored(), scoped to ONE occurrence.

    anchored() asks whether the needle occurs anywhere in the document within
    ANCHOR_WINDOW of an anchor; the index needs to know whether THIS occurrence
    does. Handing it a slice exactly ANCHOR_WINDOW wide either side gives the
    same window with no other occurrence in view, so the rule is cite_check's
    unchanged -- it is only the field of view that narrows.
    """
    w = cc.ANCHOR_WINDOW
    sl = text[max(0, start - w):end + w]
    return cc.anchored(sl, rend, anc, key, strict=strict)


def mm_occurrence(text: str, end: int) -> bool:
    """cite_check.quotes_as_mm(), scoped to ONE occurrence.

    The unit token is the whole guard against a bare 1000x sweep, and a
    DENOMINATED mm ("mm/month", "mm yr-1") is a rate, not a length.
    """
    m = cc._MM_SUFFIX.match(text, end)
    if not m:
        return False
    return not cc._MM_DENOM.match(text, m.end())


def build(docs, band: float, strict_all: bool) -> list[dict]:
    idx, keys = token_index(docs)
    rows: list[dict] = []
    seen_val: set[tuple[str, float]] = set()
    emitted: set[tuple] = set()

    for source, label, v in cc.collect_values():
        if not (abs(v) > 0):
            continue
        if (label, v) in seen_val:
            continue                       # as check_numbers de-duplicates
        seen_val.add((label, v))
        anc = cc.anchors(label)
        av = abs(v)

        # ---- metres (or whatever the value is stored in) -----------------
        for _mag, doc, rend, start, end in in_band(idx, keys, av, band):
            if not searchable_for(rend, label):
                continue
            exact = is_rounding_of(v, rend)
            # NO ANCHOR, NO BAND. cite_check's anchored() returns True when the
            # key yields no anchor tokens at all -- tolerable inside a +/-2-unit
            # window, meaningless inside a +/-25 % band, where it admits every
            # number of roughly the right size in every document. Measured on
            # report12 alone before this guard: 595 rows, the first three of
            # them a residual SD "matching" a summer-minimum shift, a slope
            # "matching" a scenario rate and a second residual SD "matching" the
            # 150 m reference distance. An unanchored occurrence is not evidence
            # of a citation; it is the inverted check the spec already ruled out.
            # The exact rendering is still indexed unanchored, because that is
            # what check_numbers' permissive path does.
            if not exact and not anc:
                continue
            strict = True if strict_all else not exact
            text = docs[doc]
            if not anchored_here(text, start, end, rend, anc, label, strict):
                continue
            k = (label, source, doc, start, "")
            if k in emitted:
                continue
            emitted.add(k)
            q = abs(float(rend))
            rows.append({
                "key": label, "source_csv": source, "committed": f"{v!r}",
                "document": doc, "quoted": rend, "dp": decimals(rend),
                "gap_pct": f"{100.0 * (q - av) / av:.4f}",
                "unit_shift": "",
                "context": norm_ctx(text[max(0, start - CTX):end + CTX]),
            })

        # ---- M31: a metre-stored value quoted in millimetres --------------
        if cc.VALUE_UNITS.get((source, label), "").lower() not in cc.METRE_UNITS:
            continue
        if not anc:
            continue                       # see the guard above
        for _mag, doc, rend, start, end in in_band(idx, keys, av * 1000.0, band):
            if not searchable_for(rend, label):
                continue
            text = docs[doc]
            if not mm_occurrence(text, end):
                continue
            # Always strict: check_numbers runs the millimetre pass strict
            # because the 1000x sweep is speculative by construction.
            if not anchored_here(text, start, end, rend, anc, label, True):
                continue
            k = (label, source, doc, start, "mm")
            if k in emitted:
                continue
            emitted.add(k)
            q = abs(float(rend)) / 1000.0
            rows.append({
                "key": label, "source_csv": source, "committed": f"{v!r}",
                "document": doc, "quoted": rend, "dp": decimals(rend),
                "gap_pct": f"{100.0 * (q - av) / av:.4f}",
                "unit_shift": "m->mm",
                "context": norm_ctx(text[max(0, start - CTX):end + CTX]),
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[3])
    ap.add_argument("--band", type=float, default=0.25,
                    help="relative band around the committed value that a "
                         "corpus number must fall in to be indexed "
                         "(default 0.25 = +/-25%%). Gaps larger than this are "
                         "not searched for and cannot appear in the output.")
    ap.add_argument("--strict-all", action="store_true",
                    help="apply cite_check's STRICT anchor (subject AND "
                         "quantity) to every candidate, not only to those that "
                         "are not the committed value correctly rounded. "
                         "Removes the asymmetry between the near-zero end of "
                         "the gap distribution and its tail.")
    ap.add_argument("--docs", action="append", default=None,
                    help="restrict the corpus to mirrors whose path contains "
                         "this substring; repeatable, matched as OR.")
    ap.add_argument("--out", default=str(OUT), help="output CSV path")
    args = ap.parse_args()

    docs = cc.load_documents()
    if args.docs:
        docs = {k: t for k, t in docs.items()
                if any(d in k for d in args.docs)}
    if not docs:
        print("No mirrors found -- run tools/refresh_mirrors.py first.")
        return 0                                   # advisory: never gates

    print(f"corpus: {len(docs)} mirror(s); band +/-{args.band * 100:g}%"
          f"{'; strict anchoring throughout' if args.strict_all else ''}")
    rows = build(docs, args.band, args.strict_all)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r["key"], r["document"],
                                             float(r["gap_pct"]))):
            w.writerow(r)
    try:
        shown = out.relative_to(REPO)
    except ValueError:
        shown = out
    print(f"  {len(rows)} row(s) written to {shown}")
    print("  Advisory only. This tool does not gate and is not in check_all.sh.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
