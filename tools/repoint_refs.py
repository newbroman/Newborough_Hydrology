#!/usr/bin/env python3
"""
repoint_refs.py — re-point typed Figure/Section cross-references after a move.

WHY IT IS NOT A FIND-AND-REPLACE, TWICE OVER

  1. The mapping is a PERMUTATION with cycles: 43 becomes 41 while 41 becomes 62.
     No ordering of sequential replacements survives that, so every occurrence is
     located first and rewritten by POSITION, last-first, in one pass.

  2. The references are not contiguous strings. Measured in report10: of 97
     "Figure ... digits" occurrences, 78 are plain text, about 15 carry a
     <text:span> style boundary between the word and the number, and 4 are the
     figure's OWN CAPTION — a <text:sequence> field that numbers itself and must
     never be rewritten. A regex over the mirror finds references the XML regex
     misses; a naive XML regex hits declarations and caption fields that are not
     references at all.

  The digits themselves are always contiguous. So the rule is: find the word,
  step over any markup, and rewrite ONLY the digit run — never the markup, and
  never a run that sits inside a caption field.

WHAT IT REFUSES TO DO

  Bare continuation numbers ("Figures 52 and 53" — the 53) are NOT matched,
  because the word that identifies them as figure references is attached to the
  first number only. They are reported instead. Guessing that a bare number
  after "and" is a figure reference is how a page number or a well count gets
  silently renumbered.

Usage:
    python3 tools/repoint_refs.py --dry-run
    python3 tools/repoint_refs.py --apply
"""
from __future__ import annotations

__version__ = "1.2.0"  # 2026-08-23. THE LOOKAHEAD BUG. v1.0 wrote (?![\d.]) to
#   stop "Figure 1.66" (a chapter-prefixed CAPTION) matching on its leading "1".
#   It also rejected every SENTENCE-FINAL reference — "shown in Figure 44." — and
#   did so in silence: 15 figure references across five documents were left on
#   their old numbers and no downstream check could see it, because a missed
#   number still falls inside the figure map. The guard now rejects a decimal
#   continuation specifically, and captions are excluded by _caption_ranges()
#   instead of by the accident of their numbering.
__version_prev__ = "1.1.0"
# 1.3.0 — 2026-08-23. --symbol-only: the "§4.9.6" form, which no pass had ever
#   read. Held back until tools/section_ref_audit.py could show, from figures
#   cited alongside, that 9 of 9 evidenced § references are stale in exactly the
#   way the plan says and that no currently-correct § reference carries a number
#   the plan would move. PIPELINE_README.md and readme.md are excluded by hand:
#   they are on an older baseline (D-067) and no § reference in either has
#   evidence either way.  # Hollingham (2026) — 2026-08-23. Tables added: a move
#   renumbers tables exactly as it renumbers figures, and the table permutation
#   is derived from the caption text by tools/table_renumber_plan.py rather than
#   typed. Caption sequence fields are now excluded BY CONSTRUCTION rather than
#   by the accident of chapter-prefixed numbering.

import argparse
import csv
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from odt_edit import edit_spans                              # noqa: E402
from refresh_mirrors import resolve                          # noqa: E402
from doc_paths import chapter_odt, REPO

REPO = Path(__file__).resolve().parents[1]
PLAN = Path(__file__).resolve().parent / "renumber_plan.csv"
PLAN_TABLE = Path(__file__).resolve().parent / "renumber_plan_table.csv"

def _versioned(stem: str) -> str:
    """The CURRENT file for a versioned document, resolved not typed.

    These paths used to be literals — "..._v1_9_45.odt". Bumping the Methods
    Supplement to v1.9.46 then broke every tool that named it, in the middle of
    check_all, with a FileNotFoundError rather than a lint failure. resolve()
    has always known which file is current; nothing was asking it. (The same
    mistake in the other direction cost a confident wrong verdict on Paper 1's
    Table 9, where `ls | tail` sorted v1_9 after v1_18.)
    """
    for src, _mirror in resolve():
        if src.name.startswith(stem):
            return str(src.relative_to(REPO))
    raise SystemExit(f"no current document found for {stem!r}")


ODTS = {
    "report8":  str(chapter_odt(8).relative_to(REPO)),
    "report9":  str(chapter_odt(9).relative_to(REPO)),
    "report10": str(chapter_odt(10).relative_to(REPO)),
    "report11": str(chapter_odt(11).relative_to(REPO)),
    "report12": str(chapter_odt(12).relative_to(REPO)),
    "Newborough_Methods_Supplement": _versioned("Newborough_Methods_Supplement"),
    "Supplementary_Material":        _versioned("Supplementary_Material"),
    "academic_Summary":              _versioned("academic_Summary"),
}
# Plain-text files that are re-pointed. changelogs/ and DECISION_LOG.md are NOT:
# they are dated records, and rewriting them would falsify what was true when
# they were written (Martin, 2026-08-23).
TEXTS = ["PIPELINE_README.md", "readme.md"]

# word, optional markup/whitespace, digit run
# The ABBREVIATED form is matched too. PIPELINE_README and readme write
# "report Fig 59" beside the full word elsewhere, and a matcher that reads only
# "Figure" moved half of each document and left the other half — which is worse
# than moving neither, because the two halves then disagree. "figure" cannot
# match here: after "fig" comes "u", and \\b requires a boundary.
FIG = re.compile(r'(?i)(\bfigures?\b|\bfigs?\.?(?=\s*\d))((?:</?[^>]+>|\s)*?)(\d{1,3})(?!\d)(?!\.\d)')
FIG_ABBR = re.compile(r'(?i)(\bfigs?\.?(?=\s*\d))((?:</?[^>]+>|\s)*?)(\d{1,3})(?!\d)(?!\.\d)')
SEC = re.compile(r'(?i)(\bsections?\b)((?:</?[^>]+>|\s)*?)(4\.\d+(?:\.\d+){0,2})(?!\d)')
TAB = re.compile(r'(?i)(\btables?\b)((?:</?[^>]+>|\s)*?)(\d{1,3})(?!\d)(?!\.\d)')
# PLURAL "Figures" governs every number in the list that follows, so the list is
# matched as a whole and each number rewritten. This is not a guess: "Figures 65
# and 66" and "Figures 63–66" are unambiguous in a way a bare trailing number is
# not (Martin, 2026-08-23). Singular "Figure 52 and 53" is NOT accepted and is
# reported instead — there the second number has no word governing it.
#
# The region is bounded to digits, separators and markup, so it stops at the
# first word. "Figures 25, 34), summer minima (Figure 32)" consumes "25, 34" and
# no further.
PLURAL = re.compile(r'(?i)(?<!script )(?<!script  )\bfigures\b'
                    r'((?:</?[^>]+>|\s|\d{1,3}|,|;|and|to|–|—|-|&)+)')
PLURAL_TAB = re.compile(r'(?i)\btables\b'
                        r'((?:</?[^>]+>|\s|\d{1,3}|,|;|and|to|–|—|-|&)+)')
NUM = re.compile(r'\d{1,3}')
RANGE = re.compile(r'(\d{1,3})\s*[–—-]\s*(\d{1,3})')

# "script figure 21-01" is a PIPELINE output, not a report figure, and its
# number is a script id. The Methods Supplement carries eight of them. None
# currently collides with a moving report number, but a matcher that cannot tell
# them apart is one renumber away from corrupting a script reference.
SCRIPT_FIG = re.compile(r'(?i)\bscript\s+figures?\b')



def _tag_spans(text: str):
    return [(m.start(), m.end()) for m in re.finditer(r"<[^>]*>", text)]


_TAG_CACHE: dict[int, list] = {}


def _in_tag(text: str, a: int, b: int) -> bool:
    """True if [a,b) intersects any markup tag."""
    key = id(text)
    spans = _TAG_CACHE.get(key)
    if spans is None:
        spans = _tag_spans(text)
        _TAG_CACHE.clear()
        _TAG_CACHE[key] = spans
    import bisect
    i = bisect.bisect_right([s for s, _ in spans], a) - 1
    if i >= 0 and spans[i][1] > a:
        return True
    if i + 1 < len(spans) and spans[i + 1][0] < b:
        return True
    return False


def load_plan(kinds):
    """Maps for the kinds asked for; every other map is returned EMPTY.

    Emptiness is the safety mechanism. Applying the figure permutation twice
    moves 63 to 56 and then moves the 56 again, so a table pass must be unable
    to touch a figure even by accident — not merely instructed not to.
    """
    fig, sec, tab = {}, {}, {}
    if {"figure", "section"} & set(kinds):
        with PLAN.open(encoding="utf8") as fh:
            for r in csv.DictReader(fh):
                if r["kind"] == "figure" and "figure" in kinds:
                    fig[r["old"]] = r["new"]
                elif r["kind"] == "section" and "section" in kinds:
                    sec[r["old"]] = r["new"]
    if "table" in kinds:
        if not PLAN_TABLE.exists():
            raise SystemExit(f"no {PLAN_TABLE.name} — run tools/table_renumber_plan.py")
        with PLAN_TABLE.open(encoding="utf8") as fh:
            for r in csv.DictReader(fh):
                tab[r["old"]] = r["new"]
    return fig, sec, tab


CAPTION_FIELD = re.compile(
    r'<text:sequence[^>]*text:name="(?:Table|Figure)"[^>]*>[^<]*</text:sequence>')


def _caption_ranges(xml: str):
    """XML spans of caption sequence fields — the numbers that number THEMSELVES.

    A caption's value is not a reference and is regenerated by the word
    processor; rewriting one desynchronises the field from its cached text. The
    first pass survived only because report9 renders captions chapter-prefixed
    ("Table 1.16"), which the digit lookahead happens to reject. report10
    renders them plain, so that is luck, not a guard.
    """
    return [(m.start(), m.end()) for m in CAPTION_FIELD.finditer(xml)]


_BLOCK_END = re.compile(
    r"</(?:text:p|text:h|text:list-item|text:list|table:table-cell"
    r"|table:table-row|table:table|draw:frame|office:annotation)>")


def _text_view(xml: str):
    """(plain text, index map) — text characters only, each mapped to its XML
    offset.

    THE REASON THIS EXISTS

      LibreOffice splits runs mid-token. report9 stores references as
      `Figure <span>6</span><span>5</span>` — the DIGITS of "65" are in two
      different elements. A regex over the raw XML sees "6", fails to find it in
      the plan, and skips the reference in silence. Twenty-three such references
      were missed on the first pass and only found because a spot check asked
      why "Figure 63" still existed (2026-08-23).

      Matching therefore happens on the text as a reader sees it, and each match
      is translated back to the one or more XML ranges it occupies.
    """
    out, idx, i, n = [], [], 0, len(xml)
    while i < n:
        if xml[i] == "<":
            k = xml.find(">", i)
            tag = xml[i:k + 1] if k >= 0 else ""
            if _BLOCK_END.match(tag):
                # A BLOCK BOUNDARY IS A WORD BOUNDARY. Stripping tags without
                # putting anything in their place runs the end of a heading
                # straight into the start of the next paragraph — the corpus
                # really contained "movementFigure 63 shows the secular
                # differential movement", and \bfigure\b cannot match there
                # because "tF" is not a boundary. Four references were invisible
                # to the 2026-08-23 re-point for exactly this reason, and no
                # check could see them: a reference nothing matches is a
                # reference nothing reports.
                #
                # The newline is synthetic, so it is mapped to the tag's own
                # offset. Nothing can ever write through it: every edit span
                # comes from a group of digits, and a digit is not a newline.
                out.append("\n"); idx.append(i)
            i = n if k < 0 else k + 1
            continue
        out.append(xml[i]); idx.append(i); i += 1
    return "".join(out), idx


def _xml_edits(idx, a: int, b: int, new: str):
    """Replacement spans for text[a:b], written into its first XML fragment."""
    runs, start, prev = [], idx[a], idx[a]
    for t in range(a + 1, b):
        if idx[t] != prev + 1:
            runs.append((start, prev + 1)); start = idx[t]
        prev = idx[t]
    runs.append((start, prev + 1))
    edits = [(runs[0][0], runs[0][1], new)]
    edits += [(s, e, "") for s, e in runs[1:]]     # digits carried by later runs
    return edits


def spans_for(text_or_xml: str, fig: dict, sec: dict, tab: dict | None = None,
              is_xml: bool = True):
    """[(start, end, new, kind, old)] in XML coordinates, plus notes."""
    tab = tab or {}
    if is_xml:
        text, idx = _text_view(text_or_xml)
        caps = _caption_ranges(text_or_xml)
    else:
        text = text_or_xml
        idx = list(range(len(text)))
        caps = []
    out, skipped, claimed = [], [], set()

    def _is_caption(s: int, e: int) -> bool:
        return any(cs <= s and e <= ce for cs, ce in caps)

    def add(a, b, new, kind, old):
        for s, e, val in _xml_edits(idx, a, b, new):
            if _is_caption(s, e):
                skipped.append(f"{kind} {old} inside a caption field — not a reference")
                return
            if (s, e) in claimed:
                return
            claimed.add((s, e))
            out.append((s, e, val, kind, old))

    for rx, table, kind in ((FIG, fig, "figure"), (SEC, sec, "section"),
                            (TAB, tab, "table")):
        for m in rx.finditer(text):
            num = m.group(3)
            new = table.get(num)
            if new is None or new == num:
                continue
            add(m.start(3), m.end(3), new, kind, num)

    for m in PLURAL.finditer(text):
        region, base = m.group(1), m.start(1)
        for rm in RANGE.finditer(region):
            lo, hi = rm.group(1), rm.group(2)
            if lo in fig or hi in fig:
                nlo, nhi = int(fig.get(lo, lo)), int(fig.get(hi, hi))
                if nhi - nlo != int(hi) - int(lo):
                    skipped.append(f"range {lo}-{hi} -> {nlo}-{nhi} not contiguous")
        for nm in NUM.finditer(region):
            num = nm.group(0)
            new = fig.get(num)
            if new is None or new == num:
                continue
            add(base + nm.start(), base + nm.end(), new, "figure", num)

    for m in PLURAL_TAB.finditer(text):
        region, base = m.group(1), m.start(1)
        for nm in NUM.finditer(region):
            num = nm.group(0)
            new = tab.get(num)
            if new is None or new == num:
                continue
            add(base + nm.start(), base + nm.end(), new, "table", num)

    for word, plan in (("figure", fig), ("table", tab)):
        rx = re.compile(rf'(?i)\b{word}\s+\d{{1,3}}\s*(?:and|,)\s*(\d{{1,3}})\b')
        for m in rx.finditer(text):
            if m.group(1) in plan:
                skipped.append(f"singular continuation '{m.group(0)[:40]}'")

    out.sort(key=lambda t: t[0])
    for (a1, b1, *_), (a2, *_) in zip(out, out[1:]):
        if b1 > a2:
            raise SystemExit(f"overlapping spans at {a1} and {a2}")
    return out, skipped


def process(name, path, fig, sec, tab, apply_):
    p = REPO / path
    is_odt = p.suffix in (".odt", ".odm")
    text = (zipfile.ZipFile(p).read("content.xml").decode("utf-8") if is_odt
            else p.read_text(encoding="utf8"))
    spans, skipped = spans_for(text, fig, sec, tab, is_xml=is_odt)
    kinds = {"figure": 0, "section": 0, "table": 0}
    for _, _, _, k, _ in spans:
        kinds[k] += 1
    print(f"  {name:<32} figure {kinds['figure']:>4}   section {kinds['section']:>4}"
          f"   table {kinds['table']:>4}"
          f"   not matched: {len(skipped)}")
    if not apply_ or not spans:
        return spans, skipped
    payload = [(a, b, new) for a, b, new, _, _ in spans]
    if is_odt:
        dst = p if p.suffix == ".odt" else p
        ok = edit_spans(p, dst, payload, expect=len(payload))
        if not ok:
            print(f"      FAILED on {name}")
    else:
        for a, b, new in reversed(payload):
            text = text[:a] + new + text[b:]
        p.write_text(text, encoding="utf8")
        print(f"      wrote {name} ({len(payload)} change(s))")
    return spans, skipped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    # Re-running --apply over an already-applied document DOUBLE-APPLIES the
    # permutation: 63 becomes 56, and a second pass reads that 56 as an old
    # number and moves it again. --only exists so a single failed document can
    # be retried without touching the ones that succeeded.
    ap.add_argument("--only", default=None,
                    help="process only documents whose key contains this string")
    # A pass is scoped to the kinds named. The figure/section pass and the table
    # pass are SEPARATE runs, because they are settled at different moments: the
    # table permutation is only derivable after the move has been made and
    # reference_lint has reported the drift.
    # THE REPAIR SWITCH. A pass already applied must not be applied again, but
    # the v1.0 lookahead left one exactly-identifiable class untouched: a
    # reference whose digits are followed by a full stop. --missed-only
    # processes THAT CLASS ONLY, so the incomplete pass can be finished without
    # moving anything the incomplete pass already moved.
    # The § form. Separate from --missed-only because it is a different class
    # for a different reason: not a bug in the matcher, a form the matcher was
    # never written to read.
    # A CORRECTION is a plan of its own. renumber_plan.csv records what was
    # applied and is not rewritten; a plan that fixes it is a separate file with
    # its own reasons, so both the error and its repair stay legible.
    ap.add_argument("--plan", default=None,
                    help="use this CSV instead of renumber_plan.csv")
    # One-off catch-up for the abbreviated form, which no pass before 1.6.0
    # could see. Same shape as --symbol-only and for the same reason.
    ap.add_argument("--abbrev-only", action="store_true",
                    help="only 'Fig 59' references; the full word is untouched")
    ap.add_argument("--symbol-only", action="store_true",
                    help="only '§4.9.6' references; figures and tables untouched")
    ap.add_argument("--missed-only", action="store_true",
                    help="only references immediately followed by '.' — repairs "
                         "a v1.0 pass, and is a no-op on anything else")
    ap.add_argument("--kind", default="figure,section",
                    help="comma-separated: figure, section, table (default "
                         "figure,section)")
    args = ap.parse_args()
    if not (args.apply or args.dry_run):
        ap.error("choose --dry-run or --apply")
    if args.symbol_only and args.missed_only:
        ap.error("--symbol-only and --missed-only are different repairs; "
                 "run them separately")
    if args.abbrev_only:
        globals()["FIG"] = FIG_ABBR
        globals()["SEC"] = re.compile(r'(?!)')
        globals()["TAB"] = re.compile(r'(?!)')
        globals()["PLURAL"] = re.compile(r'(?!)')
        globals()["PLURAL_TAB"] = re.compile(r'(?!)')
        print("  --abbrev-only: 'Fig N' references only\n")
    if args.symbol_only:
        globals()["SEC"] = re.compile(r'(§)(\s?)(4\.\d+(?:\.\d+){0,2})(?!\d)')
        globals()["FIG"] = re.compile(r'(?!)')
        globals()["TAB"] = re.compile(r'(?!)')
        globals()["PLURAL"] = re.compile(r'(?!)')
        globals()["PLURAL_TAB"] = re.compile(r'(?!)')
        print("  --symbol-only: § references only\n")
    if args.missed_only:
        globals()["FIG"] = re.compile(
            r'(?i)(\bfigures?\b)((?:</?[^>]+>|\s)*?)(\d{1,3})(?=\.)(?!\.\d)')
        globals()["TAB"] = re.compile(
            r'(?i)(\btables?\b)((?:</?[^>]+>|\s)*?)(\d{1,3})(?=\.)(?!\.\d)')
        globals()["SEC"] = re.compile(r'(?!)')          # sections were unaffected
        globals()["PLURAL"] = re.compile(r'(?!)')       # plural lists were unaffected
        globals()["PLURAL_TAB"] = re.compile(r'(?!)')
        print("  --missed-only: sentence-final references only\n")
    kinds = [k.strip().lower() for k in args.kind.split(",") if k.strip()]
    bad = set(kinds) - {"figure", "section", "table"}
    if bad:
        ap.error(f"unknown kind(s): {', '.join(sorted(bad))}")
    if args.plan:
        globals()["PLAN"] = Path(args.plan)
        print(f"  plan file: {args.plan}")
    fig, sec, tab = load_plan(kinds)
    print(f"  kinds: {', '.join(kinds)}")
    print(f"  plan: {len(fig)} figure, {len(sec)} section and {len(tab)} "
          f"table mapping(s)\n")
    tot_f = tot_s = tot_t = tot_skip = 0
    jobs = list(ODTS.items()) + [(t, t) for t in TEXTS]
    if args.only:
        # "readme.md" is a SUBSTRING of "PIPELINE_README.md", so a substring
        # filter meant for one of them silently selects both — and a second run
        # then double-applies the permutation to the first. A leading "=" asks
        # for an exact key.
        if args.only.startswith("="):
            want = args.only[1:].lower()
            jobs = [j for j in jobs if j[0].lower() == want]
        else:
            jobs = [j for j in jobs if args.only.lower() in j[0].lower()]
        print(f"  --only {args.only!r}: {len(jobs)} document(s)\n")
    review = []
    for name, rel in jobs:
        spans, skipped = process(name, rel, fig, sec, tab, args.apply)
        tot_f += sum(1 for s in spans if s[3] == "figure")
        tot_s += sum(1 for s in spans if s[3] == "section")
        tot_t += sum(1 for s in spans if s[3] == "table")
        tot_skip += len(skipped)
        review += [(name, m) for m in skipped]
    print(f"\n  TOTAL   figure {tot_f}   section {tot_s}   table {tot_t}   "
          f"left for review: {tot_skip}")
    for name, m in review:
        print(f"      {name:<32} {m}")
    if not args.apply:
        print("  dry run — nothing written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
