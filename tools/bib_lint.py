#!/usr/bin/env python3
"""
bib_lint.py
===========
Check the report bibliography against the report corpus, both directions.

WHY

  On 2026-09-08 six uncited bibliography entries were found by hand, and an
  in-text citation --- (Jennings, 1990) --- was orphaned by an edit made the
  same morning. Nothing gated either failure: an entry can sit in
  report_edits/text/report13.md forever with no citation pointing at it, and a
  citation can be typed into a chapter with no entry behind it, and both stay
  invisible until someone reads all thirteen chapters and the reference list
  side by side. This tool makes that comparison mechanical, in both
  directions, against the same mirrors the rest of the drift net already
  reads.

WHAT IT DOES NOT DO

  It does not touch any .odt, and it is not wired into check_all.sh --- the
  build brief (NRG_spec_bib_lint_2026-09-08.md) asks for one run's worth of
  Direction-B output first, so false positives in the citation-shape regexes
  can be judged before this gates anything. It is read-only, stdlib only.

Usage:
    python3 tools/bib_lint.py
    python3 tools/bib_lint.py --bib PATH           # override the bibliography mirror
    python3 tools/bib_lint.py --corpus-dir DIR     # override the corpus directory

"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) -- 2026-09-08. First issue (spec
#   NRG_spec_bib_lint_2026-09-08.md): entry -> citation and citation -> entry,
#   both directions, against the report mirrors; tools/bib_exemptions.csv
#   seeded with the six known-uncited entries. Read-only, not wired into
#   check_all.sh -- this run's Direction-B output is for review first.

import argparse
import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_BIB = REPO / "report_edits" / "text" / "report13.md"
DEFAULT_CORPUS_DIR = REPO / "report_edits" / "text"
EXEMPTIONS = REPO / "tools" / "bib_exemptions.csv"

YEAR = r"(?:1[5-9]\d{2}|20\d{2})"
PARTICLE = r"(?:van|von|de|den|der|le|la|Van|Von|De|Den|Der|Le|La)"  # sentence-initial
#   capitalisation ("Van Willegen et al. (2025)") is common and must resolve against the
#   bib's lower-case form; resolution compares surnames case-insensitively (see main()).

# Non-name capitalised words that can otherwise look like a surname sitting
# next to a bare 4-digit number (a month next to a year, a cross-reference
# kind). Direction B discards a "surname" that lands in this set.
_MONTHS = {
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
}
_STOPWORDS = _MONTHS | {
    "Figure", "Section", "Table", "Script", "Chapter", "Appendix",
    "Equation", "Page", "Note", "Volume", "Part", "Eq",
}

# An entry's own (YYYY) or (YYYYa) marker.
_ENTRY_YEAR = re.compile(r"\((" + YEAR + r"[a-z]?)\)")

# A single capitalised word -- the unit a name or a name-component is built
# from. Deliberately letters/hyphen only (no digits), which is what keeps
# codes like "MSL5" or "WMC3" from ever parsing as a surname.
_CAPWORD = r"[A-Z][A-Za-z\-]*"

# The resolving surname: an optional lower-case particle (van Asmuth, von
# Schilfgaarde) plus one capitalised word. This is deliberately ONE word --
# every first-listed author in this bibliography is (Stewart-Oaten and
# hyphenated names aside, which _CAPWORD already covers).
_FIRST_NAME = r"(?:" + PARTICLE + r"\s+)?" + _CAPWORD

# A second-or-later author's name, introduced by a connector -- may itself be
# more than one word ("Sanitwong Na Ayutthaya", "Met Office" reappearing
# in-text) since only the FIRST name is used to resolve the citation.
_CONNECTOR_NAME = _CAPWORD + r"(?:\s+" + _CAPWORD + r")*"
_CHAIN = r"(?:(?:,\s*|\s+(?:and|&)\s+)" + _CONNECTOR_NAME + r")*"

# (Surname, YYYY) / (Surname et al., YYYY) / (Surname and Surname, YYYY) /
# (Surname, Surname and Surname, YYYY) -- matched against one semicolon-split
# segment of a bracket's contents. The comma directly before the year is
# what a bracket citation always carries and a bare date range never does.
_BRACKET_CITE = re.compile(
    r"^\s*(" + _FIRST_NAME + r")" + _CHAIN + r"(?:\s+et al\.)?\s*,\s*(" + YEAR + r"[a-z]?)"
)
# A same-author trailing year in a comma list, e.g. "..., 2021, 2024)".
_MORE_YEAR = re.compile(r"^\s*,\s*(" + YEAR + r"[a-z]?)")

# Surname (YYYY) / Surname et al. (YYYY) / Surname and Surname (YYYY) /
# Surname, Surname and Surname (YYYY).
_NARRATIVE = re.compile(
    r"\b(" + _FIRST_NAME + r")" + _CHAIN + r"(?:\s+et al\.)?\s*\((" + YEAR + r"[a-z]?)\)"
)


def normalize(text: str) -> str:
    """Corpus normalisation per spec step 2: unify the dash, unify '&', drop
    backslash escapes and drop '*' emphasis markup before matching."""
    text = text.replace("‑", "-")  # non-breaking hyphen
    text = text.replace("&", "and")
    text = text.replace("\\", "")
    text = text.replace("*", "")
    return text


def starts_with_capitalised_surname(text: str) -> bool:
    m = re.match(r"^(?:%s\s+)?(\S)" % PARTICLE, text)
    if not m:
        return False
    return m.group(1).isupper()


def parse_bib(path: Path) -> list[dict]:
    """Parse the bibliography mirror. An entry is a line whose text, after
    stripping leading '*', '>' and spaces, starts with a capitalised surname
    and contains a (YYYY[a-z]?) year. Surname is the first token before the
    first comma, keeping hyphens (Stewart-Oaten); a corporate author with no
    comma before the year (Met Office, Buglife) keeps its full pre-year text."""
    entries = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = re.sub(r"^[*>\s]+", "", raw)
        if not stripped:
            continue
        ym = _ENTRY_YEAR.search(stripped)
        if not ym:
            continue
        if not starts_with_capitalised_surname(stripped):
            continue
        before = stripped[: ym.start()]
        before = re.sub(r"\*+$", "", before).strip()
        if not before:
            continue
        if "," in before:
            surname = before.split(",", 1)[0].strip()
        else:
            surname = before.strip()
        surname = re.sub(r"^\*+", "", surname).strip()
        if not surname:
            continue
        entries.append(
            {"surname": surname, "year": ym.group(1), "line": lineno, "text": stripped}
        )
    return entries


def corpus_files(corpus_dir: Path, bib_path: Path) -> list[Path]:
    files = sorted(corpus_dir.glob("report*.md"))
    return [f for f in files if f.resolve() != bib_path.resolve()]


def direction_a(entries: list[dict], corpus_lines: list[tuple[str, int, str]]) -> list[dict]:
    """entry -> citation. An entry is cited if its surname occurs, followed
    within 70 characters on the same line, by its 4-digit year. Tolerates
    'et al.', 'and X', commas and brackets in between since it is a plain
    within-window search, not a shape match."""
    findings = []
    for e in entries:
        surname_re = re.compile(re.escape(e["surname"]))
        year_re = re.compile(r"\b" + re.escape(e["year"][:4]) + r"\b")
        cited = False
        for _fname, _lineno, line in corpus_lines:
            for m in surname_re.finditer(line):
                window = line[m.end(): m.end() + 70]
                if year_re.search(window):
                    cited = True
                    break
            if cited:
                break
        if not cited:
            findings.append(e)
    return findings


def _clean_surname(s: str) -> str | None:
    s = s.strip()
    if not s or len(s) < 2:
        return None
    if any(ch.isdigit() for ch in s):
        return None
    if s in _STOPWORDS:
        return None
    return s


def _ctx(line: str, pos: int, before: int = 30, after: int = 30) -> str:
    return line[max(0, pos - before): pos + after].strip()


def direction_b(corpus_lines: list[tuple[str, int, str]], corp_names: list[str]):
    """citation -> entry. Returns every citation instance found:
    (surname, year, fname, lineno, context). corp_names are known multi-word
    corporate authors (e.g. "Met Office") from the bibliography, matched as a
    literal unit first so the single-capitalised-word regexes below cannot
    fragment "Met Office" into a bare "Office"."""
    citations = []
    for fname, lineno, line in corpus_lines:
        work = line
        for corp in corp_names:
            pat = re.compile(
                re.escape(corp) + r"(?:\s+et al\.)?\s*[,(]\s*(" + YEAR + r"[a-z]?)\)?"
            )
            for m in pat.finditer(line):
                citations.append((corp, m.group(1), fname, lineno, _ctx(line, m.start(1))))
                work = work[: m.start()] + "#" * (m.end() - m.start()) + work[m.end():]

        # Parenthetical citations, including semicolon lists of several,
        # e.g. (Rutter et al., 1971; Gash, 1979; Gash et al., 1980).
        for bm in re.finditer(r"\(([^()]*" + YEAR + r"[a-z]?[^()]*)\)", work):
            inner = bm.group(1)
            start_in_line = bm.start(1)
            offset = 0
            for seg in inner.split(";"):
                m = _BRACKET_CITE.match(seg)
                if m:
                    surname = _clean_surname(m.group(1))
                    if surname:
                        pos = start_in_line + offset + m.start(2)
                        citations.append((surname, m.group(2), fname, lineno, _ctx(line, pos)))
                        rest = seg[m.end():]
                        rpos = m.end()
                        while True:
                            m2 = _MORE_YEAR.match(rest)
                            if not m2:
                                break
                            pos2 = start_in_line + offset + rpos + m2.start(1)
                            citations.append(
                                (surname, m2.group(1), fname, lineno, _ctx(line, pos2))
                            )
                            rest = rest[m2.end():]
                            rpos += m2.end()
                offset += len(seg) + 1  # +1 for the ';' consumed by split

        # Narrative citations: Surname (YYYY) / Surname et al. (YYYY) /
        # Surname and Surname (YYYY) / Surname, Surname and Surname (YYYY).
        for nm in _NARRATIVE.finditer(work):
            surname = _clean_surname(nm.group(1))
            if surname:
                pos = nm.start(2)
                citations.append((surname, nm.group(2), fname, lineno, _ctx(line, pos)))
    return citations


def load_exemptions(path: Path) -> dict[tuple[str, str], str]:
    out = {}
    if not path.exists():
        return out
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out[(row["kind"].strip(), row["key"].strip())] = row["reason"].strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bib", type=Path, default=DEFAULT_BIB)
    ap.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS_DIR)
    args = ap.parse_args()

    bib_path: Path = args.bib
    corpus_dir: Path = args.corpus_dir

    entries = parse_bib(bib_path)
    print(f"bib_lint {__version__}")
    print(f"Bibliography: {len(entries)} entries parsed from {bib_path}")

    files = corpus_files(corpus_dir, bib_path)
    corpus_lines: list[tuple[str, int, str]] = []
    for f in files:
        text = normalize(f.read_text(encoding="utf-8"))
        for lineno, line in enumerate(text.splitlines(), 1):
            corpus_lines.append((f.name, lineno, line))

    exemptions = load_exemptions(EXEMPTIONS)
    ok = True

    print()
    print("Direction A -- entry -> citation")
    uncited = direction_a(entries, corpus_lines)
    if not uncited:
        print("  all entries cited")
    else:
        for e in uncited:
            key = f"{e['surname']} {e['year'][:4]}"
            reason = exemptions.get(("uncited", key))
            if reason is not None:
                print(f"  EXEMPT   uncited: {key}  ({reason})")
            else:
                print(f"  UNCITED: {key}  [report13.md:{e['line']}]")
                ok = False

    print()
    print("Direction B -- citation -> entry")
    corp_names = sorted(
        {e["surname"] for e in entries if " " in e["surname"]}, key=len, reverse=True
    )
    citations = direction_b(corpus_lines, corp_names)
    entry_years: dict[str, set[str]] = {}
    for e in entries:
        entry_years.setdefault(e["surname"].lower(), set()).add(e["year"][:4])

    unresolved_count = 0
    exempt_count = 0
    for surname, year, fname, lineno, ctx in citations:
        digits = year[:4]
        if digits in entry_years.get(surname.lower(), set()):
            continue
        key = f"{surname} {digits}"
        reason = exemptions.get(("unresolved", key))
        if reason is not None:
            exempt_count += 1
            print(f"  EXEMPT   unresolved: {key}  ({reason})  [{fname}:{lineno}] ...{ctx}...")
        else:
            unresolved_count += 1
            ok = False
            print(f"  UNRESOLVED: ({surname}, {year})  [{fname}:{lineno}] ...{ctx}...")
    if unresolved_count == 0 and exempt_count == 0:
        print("  all citations resolve")

    print()
    n_entries = len(entries)
    n_citations = len(citations)
    if ok:
        print(f"bib_lint: OK -- {n_entries} entries, {n_citations} citations, all resolve")
        return 0
    else:
        print(f"bib_lint: FAIL -- {n_entries} entries, {n_citations} citations, findings above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
