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

__version__ = "1.6.0"  # Hollingham (2026) — 2026-08-23. check_register():
#   the replacement column was never validated, so the register could hand a
#   displaced sense a glyph already spoken for — and had, giving z to d_depth
#   while z₀ was the datum. Exit codes split so the register gates and the
#   ambiguous backlog reports; that is what lets the tool join check_all.
#
# _superseded  # Hollingham (2026) — 2026-08-22. A QUOTED single letter
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
# DOC_GLOBS now lives in tools/doc_globs.py -- see the note there. The
# copy that used to sit here had already drifted from cite_check's.
from doc_globs import DOC_GLOBS


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
# working/DECISION_LOG.md is a DATED DELIBERATION RECORD, and the project's
# standing rule is that dated records are not rewritten — corrections go in as
# dated Notes appended, never edits in place. Twenty-four of T-01's remaining
# 128 substitutions were inside it: renaming a symbol in an entry written on
# 2026-08-13 would make the log say something nobody wrote that day, and would
# do it to the one document whose whole value is being a faithful account of
# what was decided and why. The register's job is to make the CORPUS consistent;
# the log records how the corpus got that way, quoting the notation of the time.
#
# It stays in cite_check's sweep, where it belongs: the numbers it states must
# still be true. Only the symbol rewrite is refused.
EXCLUDE_PREFIXES = ("living/", "working/DECISION_LOG.md",
                    # Generated BY a symbol tool, and its whole content is
                    # formulas quoted verbatim so the equations are visible
                    # at all. Sweeping it would report the inventory as its
                    # own backlog and never fall.
                    "notes/ledgers/EQUATION_LEDGER.md")


def _excluded(rel: str) -> bool:
    return any(rel.startswith(p) for p in EXCLUDE_PREFIXES)

CONTEXT_WINDOW = 260     # characters either side of the glyph

# Strip HTML/XML tags before counting glyphs. The character class EXCLUDES the
# newline deliberately.
#
# It was `<[^>]+>` until 2026-08-26. `[^>]` matches newlines, so a single
# unescaped `<` in prose swallowed everything up to the next `>` anywhere later
# in the file. The Methods Supplement mirror contains four such `<`, and the
# document went from 863,455 characters to 410,924 before a single symbol was
# counted — every figure this tool has ever reported for the Supplement came
# from 48% of it, and the missing 52% was silent. A tag never spans a line in
# these mirrors, so bounding the class to a line costs nothing and cannot
# swallow prose.
_MARKUP = re.compile(r"<[^>\n]+>")


def load_documents() -> dict[str, str]:
    docs: dict[str, str] = {}
    for g in DOC_GLOBS:
        for p in REPO.glob(g):
            rel = str(p.relative_to(REPO))
            if _excluded(rel):
                continue
            try:
                docs[rel] = _MARKUP.sub(" ", p.read_text(encoding="utf8"))
            except OSError:
                pass
    return docs


def load_register() -> list[dict]:
    p = REPO / REGISTER
    if not p.exists():
        sys.exit(f"no register at {REGISTER}")
    return list(csv.DictReader(p.open(encoding="utf8")))


# Glyphs that are spoken for, and by which sense. A displaced sense may not be
# re-lettered onto one of these.
#
#   z   the standard-normal test statistic. Standard usage in every statistics
#       text, so under D-055's own rule — a glyph standard in an established
#       formula keeps it, report-coined quantities yield — the statistic keeps
#       the bare letter. No register sense owns it, so no replacement may take
#       it. (D-062)
#   z₀  the drainage datum, DRAINAGE_DATUM = 3.7 m (D-055, applied).
#
# This block exists because the register handed z to d_depth while z₀ was the
# datum — re-creating, one row further down the same file, precisely the
# collision D-055 was written to kill. Nothing validated the replacement column.
RESERVED_GLYPHS = {
    "z₀": "D_datum",
    "z": None,          # owned by the test statistic, which is not a register sense
}


def check_register(senses: list[dict]) -> int:
    """Is the register self-consistent? Returns the number of STRUCTURAL faults.

    Three ways a `replacement` can be wrong, all silent until now:
      1. it is another sense's canonical glyph — the rename walks into an
         occupied seat;
      2. two displaced senses resolve to the same replacement — the rename
         creates the collision it was meant to remove;
      3. it takes a reserved glyph (see RESERVED_GLYPHS).

    A replacement in the "(rewrite as: …)" form is a prose instruction, not a
    glyph, and is skipped — that is the c_intercept precedent.
    """
    print("=" * 78)
    print("REGISTER — is the replacement column self-consistent?")
    print("=" * 78)

    canonical = {x["glyph"]: x["sense_id"]
                 for x in senses if x.get("status") == "canonical"}
    faults = 0
    seen = {}

    for sense in senses:
        rep = (sense.get("replacement") or "").strip()
        sid = sense["sense_id"]
        if not rep or rep.startswith("("):
            continue

        if rep in RESERVED_GLYPHS and RESERVED_GLYPHS[rep] != sid:
            owner = RESERVED_GLYPHS[rep]
            who = ("the sense " + owner) if owner else "the standard-normal test statistic"
            print("\n  RESERVED   %s (glyph %s) -> %r" % (sid, sense["glyph"], rep))
            print("             %r is reserved for %s" % (rep, who))
            faults += 1

        if rep in canonical and canonical[rep] != sid:
            print("\n  OCCUPIED   %s (glyph %s) -> %r" % (sid, sense["glyph"], rep))
            print("             %r is the canonical glyph of %s" % (rep, canonical[rep]))
            faults += 1

        if rep in seen:
            print("\n  DUPLICATE  %s and %s both resolve to %r" % (sid, seen[rep], rep))
            faults += 1
        else:
            seen[rep] = sid

    if faults:
        print("\n  %d structural fault(s) in %s — these gate" % (faults, REGISTER))
    else:
        print("  %d replacement(s), all distinct, none reserved or occupied" % len(seen))
    return faults


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


# Unicode subscript digits (₀-₉), subscript letters, and the ASCII forms the
# mirrors use. THE ONE DEFINITION — symbol_apply imports this rather than
# carrying its own, because two copies of a rule are two rules.
QUALIFIED_NEXT = re.compile(
    r"^(?:_|\\_|[\u2080-\u2089]|[\u2090-\u209c]|[\u1d62-\u1d6a]|\()")


_QUOTES = ("'", '"', "`", "&apos;", "&quot;", "&#39;", "&#x27;")


def is_code_literal(text: str, s0: int, e0: int) -> bool:
    """Is the occurrence a QUOTED single letter — a code literal, not a symbol?

    `occurrences()` already skips a glyph abutting a quote, added 2026-08-22
    after CLUSTER_MARKERS — matplotlib's marker codes, {1: 'o', 2: 's', 3: '^',
    4: 'D', 5: 'P'} — put a diamond marker next to DRAINAGE_DATUM in the Methods
    Supplement's constants table and the D was renamed to z₀.

    That guard reads literal quote characters. **In an ODT's content.xml the
    quotes are XML entities**, so the glyph reads as `&apos;D&apos;` and neither
    neighbouring character is a quote. The same marker table came back the
    moment the flattener stopped concatenating table cells.

    Both sides must be quoted. One side is ambiguous — an apostrophe in
    "cluster&apos;s" is not a delimiter — and over-suppressing here hides real
    symbols, which is the failure this net exists to prevent.
    """
    before, after = text[max(0, s0 - 8):s0], text[e0:e0 + 8]
    return (any(before.endswith(q) for q in _QUOTES)
            and any(after.startswith(q) for q in _QUOTES))


def is_qualified(text: str, end: int) -> bool:
    """Is the occurrence ending at `end` already qualified — subscript or argument?

    Two forms, one rule. `δ_F` is qualified by its subscript; `δ(d)` is qualified
    by its argument, which names the coastal decay function evaluated at a
    distance. Both say which quantity is meant without needing the glyph to
    change, and renaming either inserts the replacement in front of the thing
    that was doing the disambiguating: δ_cwb_F, δ_cwb(d).

    The register settles what this means: only BARE senses compete for a glyph,
    because a reader seeing δ_F is in no doubt which quantity is meant. So a
    subscripted occurrence is never work for a bare sense's rename.

    `occurrences()` still COUNTS it — for collision detection a subscripted form
    is an occurrence of the base glyph, and that is what the register's fault
    gate needs. This says only that it is not actionable, which is a different
    question and the one the proposal answers.

    Not having drawn that line cost eleven wrong substitutions in three published
    documents on 2026-08-27 (5115434): δ₀ -> δ_cwb₀, δ_F -> δ_cwb_F, and α_W —
    the van Willegen coefficient, a separate registered sense — -> α_B_W.
    """
    return bool(QUALIFIED_NEXT.match(text[end:end + 2]))


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
    register_faults = check_register(reg)
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
                    s0, e0 = span
                    # ALREADY CARRYING THE REPLACEMENT? Then it is done, and
                    # counting it as "to change" makes the headline unreachable.
                    #
                    # occurrences() gives a Greek glyph a bare re.escape with no
                    # guard, deliberately — for COLLISION detection a subscripted
                    # form is still an occurrence of the base glyph, and that is
                    # what the register's fault gate needs. But it means α inside
                    # α_B still counts, so converting α -> α_B does not reduce
                    # the count at all. Measured 2026-08-27: twenty-six
                    # substitutions were applied to six documents and the
                    # headline moved 87 -> 82, because the twenty α and δ
                    # conversions each left the glyph in place. Only the λ and L
                    # ones, where the glyph genuinely disappears, showed up.
                    #
                    # So T-01 could never have reached zero. Same shape as T-14's
                    # check, which counted markers in a document that may not be
                    # edited. A target that cannot be reached is not a target.
                    rep = (sense.get("replacement") or "").strip()
                    if rep and not rep.startswith("(") and text[s0:s0 + len(rep)] == rep:
                        table[(glyph, doc)]["canonical"] += 1
                        totals["canonical"] += 1
                        continue
                    # QUALIFIED? Counted, never proposed. See is_qualified().
                    if is_qualified(text, e0):
                        table[(glyph, doc)]["qualified"] += 1
                        totals["qualified"] += 1
                        continue
                    table[(glyph, doc)][kind] += 1
                    totals[kind] += 1
                    if kind in ("displaced", "retired"):
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
    print(f"  {'glyph':6s} {'document':46s} {'canon':>6s} {'sub':>5s} "
          f"{'displ':>6s} {'ambig':>6s}")
    for (glyph, doc), c in sorted(table.items()):
        if not sum(c.values()):
            continue
        print(f"  {glyph:6s} {doc[:45]:46s} {c['canonical']:6d} "
              f"{c['qualified']:5d} "
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
          f"qualified {totals['qualified']}   "
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

    # EXIT CODES ARE SPLIT, DELIBERATELY.
    #
    # The ambiguous list is an inherited editorial backlog — 148 entries when
    # this split was written — and gating on it would keep this tool out of
    # tools/check_all.sh forever, which is exactly where it has been. A register
    # that contradicts itself is a different kind of problem: it is wrong now,
    # it is small, and every entry is actionable. So the register gates and the
    # backlog reports.
    print()
    print("  register faults %d (gate)   ambiguous %d (advisory)"
          % (register_faults, totals["ambiguous"]))
    if register_faults:
        print("symbol_check: FAIL — the register contradicts itself")
        return 1
    print("symbol_check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
