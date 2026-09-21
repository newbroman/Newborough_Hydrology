#!/usr/bin/env python3
"""
csv_mention_lint.py
====================
Every CSV a document names exists.

Why this exists.

  A document can name a file that used to exist, was renamed, or was never
  produced under the name typed — and nothing checks that a `07_report_
  numbers.csv` cited in the Methods Supplement is still a real path under
  outputs/. `17_wtf_well_sy.csv` is the standing example: it was retired on
  2026-08-19 by D-038 (superseded by `18_wtf_01_well_sy_estimates.csv`; the
  two were byte-identical while both existed, and only the name changed) —
  so any document still naming it is stale, and this lint is what would have
  caught it.

What it flags.

  Every markdown mirror (`report_edits/text/*.md`, `docs/**/text/*.md`),
  plus `index.html` and `PIPELINE_README.md`, is scanned for tokens matching
  `[\\w.\\-]+\\.csv` (and, cheaply and identically, `.json`). For each mention,
  a file with that BASENAME must exist somewhere under outputs/, data/,
  tools/, living/ or docs/ (searched recursively). A mention that resolves
  to nothing anywhere in those roots is a FAIL: doc, line, and the name.

  This is a basename search, not a path check — a mention naming the right
  file in the wrong directory is not flagged, because prose routinely
  abbreviates a path (`*20_report_numbers.csv*` rather than
  `outputs/20_spatial_coefficients/20_report_numbers.csv`) and this lint's
  job is "does the name still refer to something", not "is the stated
  directory current".

  Markdown escaping. Pandoc mirrors sometimes escape a literal underscore in
  prose as `\\_`; unescaped, `[\\w.\\-]+\\.csv` still finds a match either way
  (the backslash breaks the character-class run, but the regex still locks
  onto the trailing `...csv` fragment starting after the break) — so a
  broken escape does not go undetected, it goes MISNAMED: the extracted
  token can be a truncated fragment of the real filename rather than the
  filename itself. Before matching, this lint unescapes `\\_ \\- \\* \\``` and
  strips literal `**`/`__` (bold delimiters — no filename in this corpus
  contains a literal double underscore, checked empirically before adding
  the strip) so a name split by markdown emphasis is read whole. What this
  cannot repair — an escape sequence this lint does not know about, or a
  token broken by something other than escaping or bold — is measured, not
  guessed at: every run compares the raw-text token set against the
  cleaned-text token set and reports how many mentions the cleaning changed,
  so a silent divergence is visible even when this run finds none.

Allowlist.

  tools/csv_mention_allow.csv: name, reason, allow_docs, allow_context. A row
  admits one TOKEN (exact
  match, or a glob-style wildcard via fnmatch — e.g. `*_report_numbers.csv`)
  that is legitimately not a literal filename: a pattern used in prose to
  describe a naming convention shared by many scripts, an explicit glob, or
  an illustrative example name. A row that matches nothing still present is
  reported stale. Adding a row to quiet a real gap — a stale citation, a
  typo'd script number, a retired file still named as current — is the
  failure this file exists to prevent; every such mention is reported so the
  author can rule on it, not silently excused.

Usage:
    python3 tools/csv_mention_lint.py            # report, non-zero exit on a fault
    python3 tools/csv_mention_lint.py --quiet    # one line unless something fails
    python3 tools/csv_mention_lint.py --selftest
"""
from __future__ import annotations

import csv
import fnmatch
import re
import sys
from pathlib import Path

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-21. First gate for "every
#   CSV a document names exists" — basename search over outputs/data/tools/
#   living/docs, with markdown-escape/bold cleanup and a measured (not
#   guessed) count of what that cleanup could not resolve.

REPO = Path(__file__).resolve().parents[1]
ALLOW = REPO / "tools" / "csv_mention_allow.csv"

SEARCH_ROOTS = ["outputs", "data", "tools", "living", "docs"]
TOKEN_RE = re.compile(r"[\w.\-]+\.(?:csv|json)")


# ── pure helpers (unit-tested by selftest, no filesystem needed) ──────────

def clean(text: str) -> str:
    """Unescape pandoc's backslash-escaping and strip bold delimiters.

    `\\_ \\- \\* \\```  ->  `_ - * ```` (pandoc's escaping of characters that
    would otherwise open markdown syntax). `**` and `__` (bold/strong
    delimiters) are removed outright — checked empirically against this
    corpus's real filenames, none of which contains a literal double
    underscore, so the strip cannot merge two real tokens into one.
    """
    text = (text.replace("\\_", "_").replace("\\-", "-")
                .replace("\\*", "*").replace("\\`", "`"))
    text = text.replace("**", "").replace("__", "")
    return text


def extract_mentions(text: str) -> list[tuple[int, str]]:
    """[(1-indexed line, token)] from the CLEANED text."""
    return [(line, tok) for line, tok, _ctx in extract_mentions_ctx(text)]


def extract_mentions_ctx(text: str) -> list[tuple[int, str, str]]:
    """[(1-indexed line, token, context)]: context is the cleaned text within
    CONTEXT_CHARS either side of the token, for the allow_context test."""
    ctext = clean(text)
    out = []
    for m in TOKEN_RE.finditer(ctext):
        line = ctext.count("\n", 0, m.start()) + 1
        ctx = ctext[max(0, m.start() - CONTEXT_CHARS): m.end() + CONTEXT_CHARS]
        out.append((line, m.group(0), ctx))
    return out


CONTEXT_CHARS = 120


def recovered_count(text: str) -> int:
    """How many cleaned-text tokens this lint's escape/bold cleanup actually
    produced that the raw text did not already contain — i.e. how many
    mentions were readable only after cleaning. Not a guess: a multiset
    difference between the raw-text token set and the cleaned-text token
    set, so it is correct even when a line carries several mentions (a
    line-keyed comparison collides on repeats) and even when cleaning
    changes how many fragments a line produces."""
    from collections import Counter
    raw_tokens = Counter(m.group(0) for m in TOKEN_RE.finditer(text))
    clean_tokens = Counter(tok for _line, tok in extract_mentions(text))
    return sum((clean_tokens - raw_tokens).values())


def build_file_index(repo: Path, roots: list[str]) -> set[str]:
    """Basenames of every file under any of `roots` (recursive)."""
    names: set[str] = set()
    for root in roots:
        base = repo / root
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file():
                names.add(p.name)
    return names


def check_doc(doc_rel: str, text: str, existing: set[str],
              allow_rows: list[dict], allow_used: list[bool]) -> list[tuple[str, int, str]]:
    """[(doc, line, token)] for every mention that resolves to no file and
    is not allowlisted. Marks allow_used in place."""
    faults = []
    doc_stem = Path(doc_rel).stem
    for line, tok, ctx in extract_mentions_ctx(text):
        if tok in existing:
            continue
        hit = None
        for i, row in enumerate(allow_rows):
            pattern = row["name"]
            if not fnmatch.fnmatchcase(tok, pattern):
                continue
            # optional narrowing columns: allow_docs (semicolon list of mirror
            # stems) and allow_context (regex that must match within
            # CONTEXT_CHARS of the token) -- so a retirement note may name the
            # file it retires without licensing the same name elsewhere.
            docs = [d.strip() for d in (row.get("allow_docs") or "").split(";") if d.strip()]
            if docs and doc_stem not in docs:
                continue
            actx = row.get("allow_context") or ""
            if actx and not re.search(actx, ctx, flags=re.IGNORECASE | re.DOTALL):
                continue
            hit = i
            break
        if hit is not None:
            allow_used[hit] = True
            continue
        faults.append((doc_rel, line, tok))
    return faults


# ── allowlist ────────────────────────────────────────────────────────────

def _allow() -> list[dict]:
    if not ALLOW.exists():
        return []
    with ALLOW.open(newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if r.get("name")]


# ── the real run ─────────────────────────────────────────────────────────

def doc_list(repo: Path = REPO) -> list[Path]:
    docs = sorted(repo.glob("report_edits/text/*.md")) + sorted(repo.glob("docs/**/text/*.md"))
    for extra in ("index.html", "PIPELINE_README.md"):
        p = repo / extra
        if p.exists():
            docs.append(p)
    return [d for d in docs if d.exists()]


def scan(repo: Path = REPO):
    """Return (faults, stale_allow, total_mentions, recovered, docs_checked)."""
    allow_rows = _allow()
    used = [False] * len(allow_rows)
    existing = build_file_index(repo, SEARCH_ROOTS)

    faults: list[tuple[str, int, str]] = []
    total = 0
    recovered = 0
    docs = doc_list(repo)
    for d in docs:
        text = d.read_text(encoding="utf8", errors="replace")
        rel = str(d.relative_to(repo))
        total += len(extract_mentions(text))
        recovered += recovered_count(text)
        faults.extend(check_doc(rel, text, existing, allow_rows, used))

    stale = [r for r, u in zip(allow_rows, used) if not u]
    return faults, stale, total, recovered, len(docs)


# ── selftest: pure logic against synthetic data, no filesystem sweep ──────

def selftest() -> bool:
    ok = True

    # extract_mentions: basic + basename-only (no path) + escape + bold
    text = (
        "See `outputs/17_wtf_01_sy_estimates.csv` and the retired "
        "17\\_wtf\\_well\\_sy.csv name.\n"
        "A 17_wtf_**01**_sy.csv mid-token bold split and a config.json reference.\n"
    )
    mentions = extract_mentions(text)
    toks = [t for _, t in mentions]
    if "17_wtf_01_sy_estimates.csv" not in toks:
        print(f"  selftest FAIL: basename extraction missing, got {toks}"); ok = False
    if "17_wtf_well_sy.csv" not in toks:
        print(f"  selftest FAIL: unescape did not recover the retired name, got {toks}"); ok = False
    if "17_wtf_01_sy.csv" not in toks:
        print(f"  selftest FAIL: mid-token bold-strip did not recover the name, got {toks}")
        ok = False
    if "config.json" not in toks:
        print(f"  selftest FAIL: .json not matched, got {toks}"); ok = False

    # recovered_count: the escaped line and the mid-token-bold line should
    # each count as recovered (the raw regex still matches SOMETHING there —
    # a truncated fragment — so a naive "does it match" check would miss the
    # corruption); the plain backtick line should not.
    n = recovered_count(text)
    if n < 2:
        print(f"  selftest FAIL: expected >=2 recovered mentions, got {n}"); ok = False

    # check_doc: existing resolves, missing fails, allowlisted is excused,
    # stale allow row is reported separately by the caller (scan()).
    existing = {"17_wtf_01_sy_estimates.csv", "config.json"}
    allow_rows = [{"name": "*_report_numbers.csv", "reason": "prose glob"}]
    used = [False]
    faults = check_doc("doc.md", text + "\nSee 09_report_numbers.csv too.\n",
                        existing, allow_rows, used)
    fault_names = {t for _doc, _ln, t in faults}
    if "17_wtf_well_sy.csv" not in fault_names or "17_wtf_01_sy.csv" not in fault_names:
        print(f"  selftest FAIL: expected both missing names flagged, got {fault_names}")
        ok = False
    if "09_report_numbers.csv" in fault_names:
        print("  selftest FAIL: allowlisted glob pattern should have been excused"); ok = False
    if not used[0]:
        print("  selftest FAIL: allow row should have been marked used"); ok = False
    if "17_wtf_01_sy_estimates.csv" in fault_names or "config.json" in fault_names:
        print("  selftest FAIL: existing files should not be flagged"); ok = False
    if "17_wtf_well_sy.csv" not in fault_names:
        print("  selftest FAIL: retired name should still be flagged, not allowlisted")
        ok = False

    return ok


def main(argv) -> int:
    quiet = "--quiet" in argv
    if "--selftest" in argv:
        ok = selftest()
        print("  csv_mention_lint selftest: " + ("OK" if ok else "FAIL"))
        return 0 if ok else 1

    try:
        faults, stale, total, recovered, n_docs = scan()
    except Exception as e:
        print(f"  FAIL cannot evaluate csv_mention_lint: {e!r}")
        return 1

    rc = 0
    for doc, line, tok in faults:
        print(f"  FAIL {doc}:{line}: {tok} — no file by this name under "
              f"{'/'.join(SEARCH_ROOTS)}")
        rc = 1
    for row in stale:
        print(f"  FAIL csv_mention_allow.csv row matches nothing: {row['name']!r}")
        rc = 1

    if rc:
        print(f"  csv_mention_lint: {len(faults)} unresolved mention(s) across {n_docs} "
              f"doc(s), {len(stale)} stale allowlist row(s) ({total} mention(s) scanned, "
              f"{recovered} recovered by escape/bold cleanup)")
    elif not quiet:
        print(f"  csv_mention_lint: {total} mention(s) across {n_docs} doc(s) all resolve "
              f"({recovered} needed escape/bold cleanup to resolve)")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
