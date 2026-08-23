#!/usr/bin/env python3
"""
number_census.py — every numeric token in the corpus, classified.

WHY THIS EXISTS, AND WHY IT IS NOT ANOTHER INDEX

  `citation_index.csv` catalogues numbers that somebody has confirmed: 238 rows
  against roughly a thousand published pipeline values, and every row costs a
  human adjudication because the builder's proposals are about half coincidence.
  Cataloguing the whole corpus that way does not converge — the queue grows
  faster than it clears.

  Martin's requirement is the right one: **every number should be traceable.**
  This tool delivers it by INVERTING THE DEFAULT. Instead of asking "which
  numbers have been catalogued", it asks "which numbers have NOT been accounted
  for", and it accounts for a number in one of six ways:

    INDEXED      a citation_index.csv row already pins this document's quotation
    PIPELINE     it renders a committed pipeline value, near that value's anchors
                 (metres quoted in millimetres included — see M31 / D-066)
    STRUCTURAL   it is a pointer, not a measurement: Section 4.6, Figure 21,
                 Table 8, Step 41, Script 25, §S.15, Phase 3, Appendix B
    DATE         a year, a month-year, or a date in a range
    CITATION     a year inside a reference entry or an (Author, 2013) construct
    UNCLASSIFIED everything else

  **UNCLASSIFIED is the number that matters.** It is the corpus's untraced
  surface, it is measurable today, and it can only go down. That is a property
  a coverage percentage does not have: coverage rises when the index grows AND
  when documents shrink, so it can improve while the problem gets worse.

  Nothing here adjudicates. A token classified PIPELINE is a token that renders
  a committed value near its anchors — the same evidence `cite_check` acts on,
  no stronger. The census says what is accounted for, not what is correct.

WHAT IT DELIBERATELY DOES NOT DO

  It does not classify p-values, confidence bounds, sample sizes or R² as
  "statistics" and wave them through. Those are pipeline values more often than
  not, and a bucket that swallowed them would hide exactly the numbers most
  worth tracing. They stay UNCLASSIFIED until they are indexed or matched.

Usage:
    python3 tools/number_census.py                  # per-document table
    python3 tools/number_census.py --sample 40      # unclassified, in context
    python3 tools/number_census.py --csv out.csv    # every token, classified
    python3 tools/number_census.py --baseline       # write the committed baseline
    python3 tools/number_census.py --gate           # fail if unclassified rose
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-23. First issue.

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cite_check as cc                                   # noqa: E402

REPO = cc.REPO
BASELINE = Path(__file__).resolve().parent / "number_census_baseline.json"

# A numeric token: an optional sign, digits, optional thousands separators and
# an optional decimal part. Percent and unit suffixes are NOT consumed — the
# classifier reads them from the following context instead.
_TOKEN = re.compile(r"(?<![\w.])[+\-−]?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\w])"
                    r"|(?<![\w.])[+\-−]?\d+(?:\.\d+)?(?![\w])")

# Pointer words. A number after one of these is an address, not a measurement.
_STRUCTURAL_BEFORE = re.compile(
    r"(?i)(section|sections|§+|fig\.?|figure|figures|table|tables|panel|step|steps|"
    r"script|scripts|phase|phases|appendix|eq\.?|equation|chapter|page|pp?\.|"
    r"tier|cluster|c|paper|note|item|row|column|col\.?|version|v)\s*[SsFf]?[\d.]*$")

_YEAR = re.compile(r"^(19|20)\d{2}$")
_MONTHS = (r"jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
           r"january|february|march|april|june|july|august|september|october|"
           r"november|december|spring|summer|autumn|winter")
_DATE_NEAR = re.compile(r"(?i)(%s)\W{0,3}$" % _MONTHS)
_DATE_AFTER = re.compile(r"(?i)^\W{0,3}(%s)" % _MONTHS)
# A year range: 2005–2026, 1989-96, 2011/12
_RANGE = re.compile(r"^\s*[–—\-/]\s*\d{2,4}")

# Mirror artefacts. These are not corpus content — they are pandoc's own output.
# Counting them made the first census read 62.6% untraced, and the single largest
# contributor was `[]{#anchor-329}`. A census that inflates itself with the
# converter's bookkeeping cannot be driven down by anyone.
_ARTEFACT = re.compile(
    r"\[\]\{#[^}]*\}"                     # []{#anchor-329}, []{#section-4}
    r"|\{width=\"[^\"]*\"[^}]*\}"          # {width="15.8cm" height="9.7cm"}
    r"|\]\(Pictures/[^)]*\)"                # ](Pictures/10000000000...jpg)
    r"|\]\(media/[^)]*\)"
    r"|#anchor-\d+"
    r"|\bT\d+\b"                           # text:style-name residue
)

# Journal pagination: "Ecological Applications, 4(1), 16--30." — a volume, an
# issue and a page range. Three numbers per reference entry, none of them a
# measurement, and the corpus carries hundreds.
_PAGINATION = re.compile(
    r"(?i)(?:\b\d+\s*\(\s*\d+\s*\)\s*,?\s*\d+\s*[–—-]{1,2}\s*\d+"
    r"|\bpp?\.\s*\d+\s*[–—-]{1,2}\s*\d+"
    r"|\b\d+\s*[–—-]{1,2}\s*\d+\s*\.\s*(?:doi|https?)"
    r"|\bdoi:\s*\S+"
    r"|\bhttps?://\S+"
    r"|\bISBN\s*\S+)")

# Ledger and output-file identifiers: 25_05, 10a_02, 37b, S.15c, F.6.
_IDENTIFIER = re.compile(r"\b\d{1,2}[a-z]?_\d{1,2}\w*|\b[SF]\.\d+[a-z]?\b")

CLASSES = ["INDEXED", "PIPELINE", "STRUCTURAL", "DATE", "CITATION", "ARTEFACT",
           "UNCLASSIFIED"]


def _masked_spans(text: str) -> list[tuple[int, int]]:
    """Character ranges whose numbers are not corpus content."""
    spans = []
    for rx in (_ARTEFACT, _PAGINATION, _IDENTIFIER):
        spans.extend((m.start(), m.end()) for m in rx.finditer(text))
    return sorted(spans)


def _in_spans(spans: list[tuple[int, int]], a: int, b: int) -> bool:
    lo, hi = 0, len(spans)
    while lo < hi:
        mid = (lo + hi) // 2
        s, e = spans[mid]
        if e <= a:
            lo = mid + 1
        elif s >= b:
            hi = mid
        else:
            return True
    return False


def _load_index() -> dict[str, set[str]]:
    """document -> {quoted strings already pinned by citation_index.csv}."""
    out: dict[str, set[str]] = {}
    p = REPO / "tools" / "citation_index.csv"
    if not p.exists():
        return out
    with p.open(encoding="utf8") as fh:
        for row in csv.DictReader(fh):
            if (row.get("status") or "").strip().lower() == "rejected":
                continue
            out.setdefault(row["document"], set()).add((row.get("quoted") or "").strip())
    return out


def _build_rendering_map() -> dict[str, list[str]]:
    """rendering string -> [labels that render to it].

    Built ONCE. Scanning every value against every document is what makes
    cite_check slow; the census reverses the lookup so each token is answered
    from a dict.
    """
    ren: dict[str, list[str]] = {}
    seen: set[tuple[str, float]] = set()
    for source, label, v in cc.collect_values():
        if not (abs(v) > 0) or (label, v) in seen:
            continue
        seen.add((label, v))
        dps = [0, 2, 3, 4] if (float(v).is_integer() or abs(v) >= cc.LARGE_VALUE_MIN) \
            else [2, 3, 4]
        strings = [cc.render(v, dp) for dp in dps]
        if cc.VALUE_UNITS.get((source, label), "").lower() in cc.METRE_UNITS:
            strings += cc.mm_renderings(v)
        for s in strings:
            if cc.searchable(s, label):
                ren.setdefault(s.lstrip("+-−"), []).append(label)
    return ren


def _is_citation_context(text: str, a: int, b: int) -> bool:
    """A year inside a reference entry or an (Author, 2013) construct."""
    before = text[max(0, a - 90):a]
    after = text[b:b + 4]
    if re.search(r"[A-Z][a-z]+(?:\s+(?:and|&|et al\.?))?[^.]{0,40},\s*$", before):
        return True
    if re.search(r"\(\s*[A-Z][A-Za-z’'\-]+[^()]{0,60},\s*$", before) and after.startswith(")"):
        return True
    if re.search(r"(?i)(doi|https?://|isbn|pp\.)", before[-40:]):
        return True
    return False


def classify(doc: str, text: str, ren: dict[str, list[str]],
             indexed: set[str]) -> list[tuple[int, str, str]]:
    """[(position, token, class)] for every numeric token in one document."""
    out = []
    spans = _masked_spans(text)
    for m in _TOKEN.finditer(text):
        a, b = m.span()
        tok = m.group(0)
        bare = tok.lstrip("+-−")
        if _in_spans(spans, a, b):
            out.append((a, tok, "ARTEFACT")); continue
        before = text[max(0, a - 60):a]
        after = text[b:b + 30]

        if tok in indexed or bare in indexed:
            out.append((a, tok, "INDEXED")); continue

        labels = ren.get(bare) or ren.get(bare.replace(",", ""))
        if labels and any(cc.anchored(text, tok, cc.anchors(lab), lab, strict=True)
                          for lab in labels[:6]):
            out.append((a, tok, "PIPELINE")); continue

        if _STRUCTURAL_BEFORE.search(before):
            out.append((a, tok, "STRUCTURAL")); continue

        if _YEAR.match(bare):
            if _is_citation_context(text, a, b):
                out.append((a, tok, "CITATION")); continue
            out.append((a, tok, "DATE")); continue

        if _DATE_NEAR.search(before) or _DATE_AFTER.match(after) or _RANGE.match(after):
            out.append((a, tok, "DATE")); continue

        out.append((a, tok, "UNCLASSIFIED"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0,
                    help="print N unclassified tokens with surrounding context")
    ap.add_argument("--csv", default=None, help="write every token and its class")
    ap.add_argument("--baseline", action="store_true",
                    help="write the committed baseline this run becomes")
    ap.add_argument("--gate", action="store_true",
                    help="exit non-zero if UNCLASSIFIED rose above the baseline")
    args = ap.parse_args()

    docs = cc.load_documents()
    ren = _build_rendering_map()
    index = _load_index()

    print("=" * 78)
    print("NUMBER CENSUS — every numeric token in the corpus, classified")
    print("=" * 78)
    print(f"  {len(docs)} document(s); {len(ren)} distinct pipeline rendering(s)")
    print()

    per_doc, rows, unclassified_ctx = {}, [], []
    for doc, text in sorted(docs.items()):
        got = classify(doc, text, ren, index.get(doc, set()))
        counts = {c: 0 for c in CLASSES}
        for pos, tok, cls in got:
            counts[cls] += 1
            rows.append((doc, pos, tok, cls))
            if cls == "UNCLASSIFIED":
                ctx = text[max(0, pos - 55):pos + len(tok) + 45]
                unclassified_ctx.append((doc, tok, " ".join(ctx.split())))
        per_doc[doc] = counts

    w = max(len(Path(d).name) for d in per_doc) + 2
    hdr = f"  {'document':<{w}}" + "".join(f"{c[:5]:>8}" for c in CLASSES) + f"{'total':>8}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    tot = {c: 0 for c in CLASSES}
    for doc in sorted(per_doc, key=lambda d: -per_doc[d]["UNCLASSIFIED"]):
        c = per_doc[doc]
        n = sum(c.values())
        for k in CLASSES:
            tot[k] += c[k]
        print(f"  {Path(doc).name:<{w}}" + "".join(f"{c[k]:>8}" for k in CLASSES) + f"{n:>8}")
    grand = sum(tot.values())
    print("  " + "-" * (len(hdr) - 2))
    print(f"  {'TOTAL':<{w}}" + "".join(f"{tot[k]:>8}" for k in CLASSES) + f"{grand:>8}")

    unc = tot["UNCLASSIFIED"]
    corpus_n = grand - tot["ARTEFACT"]
    print(f"\n  UNCLASSIFIED: {unc} of {corpus_n} corpus numeric tokens "
          f"({100.0 * unc / max(1, corpus_n):.1f}%) are not yet traceable to a "
          f"source, a pointer or a date.")
    print(f"  ({tot['ARTEFACT']} further token(s) are pandoc/ledger artefacts and "
          f"are not corpus content.)")
    print("  This is the number to drive down. It cannot be improved by deleting text.")

    if args.sample:
        print("\n  UNCLASSIFIED SAMPLE")
        step = max(1, len(unclassified_ctx) // args.sample)
        for doc, tok, ctx in unclassified_ctx[::step][:args.sample]:
            print(f"    {Path(doc).name:<34} {tok:>10}   …{ctx}…")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf8") as fh:
            wr = csv.writer(fh)
            wr.writerow(["document", "position", "token", "class"])
            wr.writerows(rows)
        print(f"\n  wrote {len(rows)} row(s) to {args.csv}")

    if args.baseline:
        BASELINE.write_text(json.dumps(
            {"total": grand, "by_class": tot,
             "by_document": {d: per_doc[d]["UNCLASSIFIED"] for d in per_doc}},
            indent=2, sort_keys=True), encoding="utf8")
        print(f"  baseline written to {BASELINE.name}")

    if args.gate:
        if not BASELINE.exists():
            print("\n  no baseline — run --baseline first")
            return 1
        base = json.loads(BASELINE.read_text(encoding="utf8"))
        was = base["by_class"]["UNCLASSIFIED"]
        if unc > was:
            print(f"\n  FAIL: UNCLASSIFIED rose {was} -> {unc}")
            worse = [(d, per_doc[d]["UNCLASSIFIED"] - base["by_document"].get(d, 0))
                     for d in per_doc
                     if per_doc[d]["UNCLASSIFIED"] > base["by_document"].get(d, 0)]
            for d, delta in sorted(worse, key=lambda r: -r[1]):
                print(f"      +{delta:<5} {d}")
            return 1
        print(f"\n  number_census: OK ({was} -> {unc})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
