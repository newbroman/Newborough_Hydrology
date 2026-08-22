"""
symbol_check.py — the drift net for symbols, alongside cite_check for numbers.

A number can be checked against a committed CSV. A symbol cannot: what makes a
symbol right or wrong is that it means one thing, everywhere, and that where a
glyph is standard in an established formula the established use keeps it. So this
tool does not compare values. It reads a register of glyph senses, finds every
occurrence of every registered glyph across the corpus, and asks which sense each
occurrence belongs to.

Three outcomes per occurrence:

  CANONICAL   the context matches the sense that keeps the glyph. Nothing to do.
  DISPLACED   the context matches a sense the register says must yield. This is
              an edit: the occurrence should carry the replacement symbol.
  AMBIGUOUS   no sense's context matched, or more than one did. This is the
              review list, and it is the point of the exercise — an occurrence a
              machine cannot classify is one a reader cannot either.

Nothing is edited. The tool emits a proposal, because a symbol rename applied
blind is worse than a stale number: it changes what an equation says without
changing anything a proof-reader would notice.

Register: tools/symbol_register.csv
    glyph        the character as it appears in the documents
    sense_id     unique id for this meaning
    form         bare | subscripted. Only BARE senses compete for a glyph: a
                 reader seeing D_fell is in no doubt, and a subscripted sense is
                 recorded so the register is complete, not because it collides
    meaning      what the glyph denotes in this sense
    units        units, or "dimensionless"
    status       canonical | displaced | retired
    replacement  the symbol a displaced sense becomes (blank if canonical)
    context_any  pipe-separated phrases; the sense matches when any occurs
                 within CONTEXT_WINDOW characters of the glyph
    defined_in   where the sense is defined

Usage
    python3 tools/symbol_check.py                 audit + occurrence table
    python3 tools/symbol_check.py --proposal out.csv   write the edit proposal
    python3 tools/symbol_check.py --glyph λ       one glyph only
"""

from __future__ import annotations

__version__ = "1.5.0"  # Hollingham (2026) — 2026-08-22. A QUOTED single letter
#   is a code literal, not a symbol. CLUSTER_MARKERS in the Methods Supplement
#   lists matplotlib's marker codes — {1: 'o', 2: 's', 3: '^', 4: 'D', 5: 'P'} —
#   and the constants table puts DRAINAGE_DATUM in the next row, so the D of the
#   diamond marker classified as the drainage datum and symbol_apply renamed it.
#   Caught by scanning the applied result for z₀ inside quotes; the document was
#   reverted at that cell. A glyph abutting a quote or a backtick on either side
#   is now skipped.
#
# v1.4.0  # Hollingham (2026) — 2026-08-21. Two classes of false
#   occurrence removed from the Latin guard. The ASCII character class could not
#   see a Welsh letter, so the D of "Dŵr Daear" in the Welsh summary counted as
#   the datum; the class is now Unicode, and a glyph abutting any letter in any
#   script is skipped. The identifier guard also only excluded a digit after the
#   hyphen (D-011), so "superseded-by D-nnn", "D-numbers" and "D-id" in the
#   Decision Log were each counted as the symbol; a letter after the hyphen is
#   now excluded too. Working the ambiguous list is what surfaced both: five of
#   the sixteen surviving D's were not symbols at all.
#
# v1.3.0  # Hollingham (2026) — 2026-08-21. The guard now also
#   excludes LaTeX subscript forms — D_{\\mathit{fell}} and D_x — which were
#   the bulk of what survived as ambiguous D. Working that residue also turned
#   up a FOURTH bare sense of D, the inferred scrape excavation depth H0/Sy,
#   now registered: the audit found a collision the symbol list had missed.
#
# v1.2.0  # Hollingham (2026) — 2026-08-21. Adds the `form` column.
#   Working the ambiguous list showed most D "collisions" were D_fell, D_scrape
#   and D_residual — subscripted, and no reader is in doubt about those. Only
#   BARE senses compete for a glyph; subscripted ones are registered so the list
#   is complete and skipped in the audit. The Latin guard also drops anything
#   followed by a full stop, which was counting author initials in the
#   bibliographies as occurrences of D.
#
# v1.1.0  # Hollingham (2026) — 2026-08-21. Tighter guard on bare
#   Latin letters. A single letter is usually not a symbol: identifier forms
#   (D-011), list markers and column letters were all counting as occurrences,
#   and the Decision Log alone contributed a hundred false D's. Greek glyphs
#   were never affected — they are self-delimiting, which is why the Greek
#   counts were trustworthy from the first run and the Latin ones were not.
#
# v1.0.0  # Hollingham (2026) — 2026-08-21. First issue.

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REGISTER = "tools/symbol_register.csv"

# Kept in step with cite_check.DOC_GLOBS: a document outside this list is
# invisible to both nets, and the two should never diverge.
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

CONTEXT_WINDOW = 260     # characters either side of the glyph
_MARKUP = re.compile(r"<[^>]+>")


def load_documents() -> dict[str, str]:
    docs: dict[str, str] = {}
    for g in DOC_GLOBS:
        for p in REPO.glob(g):
            try:
                docs[str(p.relative_to(REPO))] = _MARKUP.sub(" ", p.read_text(encoding="utf8"))
            except OSError:
                pass
    return docs


def load_register() -> list[dict]:
    p = REPO / REGISTER
    if not p.exists():
        sys.exit(f"no register at {REGISTER}")
    return list(csv.DictReader(p.open(encoding="utf8")))


def occurrences(text: str, glyph: str):
    """Spans of `glyph` used AS A SYMBOL, not as a letter inside a word.

    Latin letters need the guard — D in DGPS is not the datum — while Greek
    letters are effectively self-delimiting. Subscripted forms (φ_F, β₃) count
    as occurrences of the base glyph, because the collision is in the glyph.
    """
    if glyph.isascii() and glyph.isalpha():
        # A bare Latin letter is mostly not a symbol. Excluded: identifier forms
        # (D-011, RB-14), list markers (a) b) c)), table-column letters followed
        # by a full stop, and anything abutting a word character. Without these
        # the Decision Log alone contributes a hundred false occurrences of D
        # and the counts stop meaning anything.
        pat = re.compile(
            rf"(?<![^\W\d_]|[0-9_\-]|['\"`]){re.escape(glyph)}"
            r"(?![^\W\d_]|-[^\W_]|\)|\.|\d|\\_|_\{|_[A-Za-z]|['\"`])")
    else:
        pat = re.compile(re.escape(glyph))
    return [(m.start(), m.end()) for m in pat.finditer(text)]


def classify(text: str, span, senses: list[dict]) -> list[str]:
    """Which registered senses the context around `span` matches."""
    s, e = span
    window = text[max(0, s - CONTEXT_WINDOW): e + CONTEXT_WINDOW].lower()
    hits = []
    for sense in senses:
        phrases = [p.strip().lower() for p in sense["context_any"].split("|") if p.strip()]
        if any(p in window for p in phrases):
            hits.append(sense["sense_id"])
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--proposal", help="write the edit proposal to this CSV")
    ap.add_argument("--glyph", help="restrict to one glyph")
    ap.add_argument("--show-ambiguous", type=int, default=6,
                    help="how many ambiguous contexts to print per glyph")
    args = ap.parse_args()

    reg = load_register()
    if args.glyph:
        reg = [r for r in reg if r["glyph"] == args.glyph]
        if not reg:
            sys.exit(f"glyph {args.glyph!r} is not in the register")
    docs = load_documents()
    by_glyph: dict[str, list[dict]] = defaultdict(list)
    for r in reg:
        by_glyph[r["glyph"]].append(r)

    print("=" * 78)
    print(f"SYMBOL AUDIT — {len(by_glyph)} glyph(s), {len(reg)} registered sense(s), "
          f"{len(docs)} documents")
    print("=" * 78)

    proposal, ambiguous_examples = [], defaultdict(list)
    totals = Counter()
    table: dict[tuple[str, str], Counter] = defaultdict(Counter)

    n_sub = sum(1 for r in reg if r.get("form") == "subscripted")
    if n_sub:
        print(f"\n  {n_sub} subscripted sense(s) registered and not audited: a "
              f"reader seeing D_fell is in no doubt which quantity is meant, so "
              f"they do not compete for the glyph.")
    for glyph, senses in sorted(by_glyph.items()):
        senses = [s for s in senses if s.get("form", "bare") == "bare"]
        if not senses:
            continue
        canonical = [s for s in senses if s["status"] == "canonical"]
        print(f"\n  {glyph}   {len(senses)} registered sense(s)"
              f"{'  — no canonical sense declared' if not canonical else ''}")
        for s in senses:
            mark = {"canonical": "keeps the glyph", "displaced": f"-> {s['replacement']}",
                    "retired": "retired"}.get(s["status"], s["status"])
            print(f"        {s['sense_id']:22s} {mark:24s} {s['meaning'][:44]}")
        for doc, text in sorted(docs.items()):
            for span in occurrences(text, glyph):
                hits = classify(text, span, senses)
                if len(hits) == 1:
                    sense = next(s for s in senses if s["sense_id"] == hits[0])
                    kind = sense["status"]
                    table[(glyph, doc)][kind] += 1
                    totals[kind] += 1
                    if kind in ("displaced", "retired"):
                        s0, e0 = span
                        proposal.append({
                            "glyph": glyph, "sense_id": sense["sense_id"],
                            "replacement": sense["replacement"], "document": doc,
                            "offset": s0,
                            "context": re.sub(r"\s+", " ",
                                              text[max(0, s0 - 70):e0 + 70]).strip(),
                        })
                else:
                    table[(glyph, doc)]["ambiguous"] += 1
                    totals["ambiguous"] += 1
                    s0, e0 = span
                    if len(ambiguous_examples[glyph]) < args.show_ambiguous:
                        ambiguous_examples[glyph].append(
                            (doc, len(hits), re.sub(r"\s+", " ",
                                                    text[max(0, s0 - 90):e0 + 90]).strip()))

    print("\n" + "=" * 78)
    print("OCCURRENCE TABLE — counts by glyph and document")
    print("=" * 78)
    print(f"  {'glyph':6s} {'document':46s} {'canon':>6s} {'displ':>6s} {'ambig':>6s}")
    for (glyph, doc), c in sorted(table.items()):
        if not sum(c.values()):
            continue
        print(f"  {glyph:6s} {doc[:45]:46s} {c['canonical']:6d} "
              f"{c['displaced'] + c['retired']:6d} {c['ambiguous']:6d}")

    print("\n" + "=" * 78)
    print("AMBIGUOUS — the review list")
    print("=" * 78)
    print("  An occurrence no context rule could place. Either the register needs a"
          "\n  phrase it lacks, or the document does not say which quantity it means —"
          "\n  and the second is the finding worth having.")
    for glyph, examples in sorted(ambiguous_examples.items()):
        print(f"\n  {glyph}:")
        for doc, n, ctx in examples:
            why = "no sense matched" if n == 0 else f"{n} senses matched"
            print(f"      [{why}] {doc}")
            print(f"        ...{ctx[:150]}...")

    print("\n" + "=" * 78)
    print(f"  canonical {totals['canonical']}   "
          f"to change {totals['displaced'] + totals['retired']}   "
          f"ambiguous {totals['ambiguous']}")
    if args.proposal:
        with open(args.proposal, "w", newline="", encoding="utf8") as fh:
            w = csv.DictWriter(fh, fieldnames=["glyph", "sense_id", "replacement",
                                               "document", "offset", "context"])
            w.writeheader()
            w.writerows(proposal)
        print(f"  proposal written to {args.proposal} ({len(proposal)} edit(s))")
    print("  Nothing has been changed. Review the proposal before any edit.")
    return 1 if totals["ambiguous"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
