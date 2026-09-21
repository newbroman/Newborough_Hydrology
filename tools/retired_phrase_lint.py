#!/usr/bin/env python3
"""
retired_phrase_lint.py
=======================
A retired wording or a retired number does not get to reappear in the
document corpus just because nobody remembered it was retired.

Why this exists.

  CLAUDE.md's "Retired and corrected quantities" section and the project's
  own working rules carry a growing list of phrasings and figures that were
  true once and are wrong now: tau (Sy/beta_3) called a "residence time" or
  a "drainage timescale"; t half described as the aquifer's memory; 117
  "measuring points" quoted as if it were a well count; a 1,172 ha bounding
  box or an 8.4 ha clearfell area that a KML correction superseded; a stale
  Thornthwaite latitude; a stale pipeline step count; a Pye & Blott figure
  Martin does not own; the em space character; and a monthly reading typed
  as a YYYY-MM-DD date rather than "Month YYYY" (SSM Formulation reference).
  Every one of these is a rule written down in prose, in a file nobody
  greps before writing a sentence, which is exactly how a retired figure
  gets requoted: the sentence reads as settled fact and nothing checks it
  against the retirement. This lint is the check.

What it flags.

  For each row in tools/retired_phrases.csv, a case-insensitive regex is
  scanned across every markdown mirror in the corpus. A row's `severity` is
  `gate` (fails the run) or `advisory` (printed as a NOTE, never fails it) --
  the date row (RP-12) is advisory because "is this hit a monthly reading
  mistyped, or a genuine daily date (an imagery frame, a felling/scrape
  event)?" is a judgement call the admission list can only approximate, not
  settle.

  Two independent ways to admit an occurrence:
    - `allow_docs`: a semicolon list of mirror stems where the ENTIRE
      pattern is permitted, however it appears in that document.
    - `allow_context`: a regex that, if it matches within 60 characters
      BEFORE the hit, admits that one occurrence wherever it appears. RP-01
      and RP-02 use this to admit the corpus's own explanations of the
      retirement ("...is not a residence time", "...not to be called a
      drainage timescale") without admitting a fresh assertion that tau IS
      one; RP-12 uses it for the frame/event/survey vocabulary that marks a
      genuinely daily date.

  Neither mechanism is a way to make a real hit disappear quietly: every
  admitted occurrence is a claim, in the CSV, about why that specific text
  is not the retired wording -- argue it there, not by loosening the
  pattern. If a GATE row hits text that is not already admitted, that is
  what this tool exists to surface, not a bug in the pattern.

Corpus.

  report_edits/text/*.md, docs/**/text/*.md (recursive), index.html and
  PIPELINE_README.md at the repository root. Every mirror discovered this
  way is scanned; nothing in that set is skipped.

Allowlist and staleness.

  Every CSV regex is compiled at load; a pattern that does not compile is a
  FAIL, not a silent skip. Every `allow_docs` stem must name a mirror that
  currently exists in the corpus -- a stem that matches nothing is a stale
  exemption and is a FAIL, on the same argument as season_lint's stale
  EXEMPT entries and xref_lint's stale allow rows: "the file cannot
  silently outlive the text it excuses."

Usage:
    python3 tools/retired_phrase_lint.py            # report, exit 1 on a fault
    python3 tools/retired_phrase_lint.py --quiet     # only faults/notes
    python3 tools/retired_phrase_lint.py --selftest
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-21. First issue: gates
#   CLAUDE.md's "Retired and corrected quantities" and the related
#   non-negotiables (no Pye & Blott figure, no em space, no YYYY-MM-DD for
#   monthly data) against the markdown mirror corpus.

import argparse
import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CSV_PATH = REPO / "tools" / "retired_phrases.csv"

VALID_KINDS = {"phrase", "number", "char", "date"}
VALID_SEVERITIES = {"gate", "advisory"}

CONTEXT_WIDTH = 60          # chars either side, for the printed context
ALLOW_CONTEXT_WIDTH = 60    # chars BEFORE the hit that allow_context scans


def find_mirrors(repo: Path = REPO) -> list[Path]:
    mirrors = (sorted(repo.glob("report_edits/text/*.md"))
               + sorted(repo.glob("docs/**/text/*.md"))
               + [repo / "index.html", repo / "PIPELINE_README.md"])
    return [m for m in mirrors if m.exists()]


def load_rows(csv_path: Path = CSV_PATH) -> tuple[list[dict], list[str]]:
    """Return (rows, load_faults). A load fault is a reason the CSV itself
    is broken -- a regex that will not compile, a kind or severity outside
    the closed vocabulary -- distinct from a fault found while scanning."""
    rows: list[dict] = []
    faults: list[str] = []
    if not csv_path.exists():
        return rows, [f"{csv_path}: does not exist"]
    with csv_path.open(newline="", encoding="utf-8") as fh:
        for i, row in enumerate(csv.DictReader(fh), start=2):  # header is line 1
            rid = row.get("id") or f"<row {i}>"
            pattern = row.get("pattern") or ""
            try:
                compiled = re.compile(pattern, re.IGNORECASE)
            except re.error as exc:
                faults.append(f"{rid}: pattern does not compile: {exc}")
                compiled = None
            kind = (row.get("kind") or "").strip()
            if kind not in VALID_KINDS:
                faults.append(f"{rid}: kind {kind!r} not one of {sorted(VALID_KINDS)}")
            severity = (row.get("severity") or "").strip()
            if severity not in VALID_SEVERITIES:
                faults.append(f"{rid}: severity {severity!r} not one of {sorted(VALID_SEVERITIES)}")
            allow_context_raw = (row.get("allow_context") or "").strip()
            allow_context = None
            if allow_context_raw:
                try:
                    allow_context = re.compile(allow_context_raw, re.IGNORECASE)
                except re.error as exc:
                    faults.append(f"{rid}: allow_context does not compile: {exc}")
            allow_docs = [d.strip() for d in (row.get("allow_docs") or "").split(";") if d.strip()]
            rows.append({
                "id": rid,
                "pattern_src": pattern,
                "compiled": compiled,
                "kind": kind,
                "reason": row.get("reason") or "",
                "allow_docs": allow_docs,
                "allow_context": allow_context,
                "severity": severity,
            })
    return rows, faults


def check_stale_allow_docs(rows: list[dict], mirrors: list[Path]) -> list[str]:
    stems = {m.stem for m in mirrors}
    faults = []
    for row in rows:
        for stem in row["allow_docs"]:
            if stem not in stems:
                faults.append(
                    f"{row['id']}: allow_docs stem {stem!r} names no mirror in the "
                    f"current corpus")
    return faults


def _context(text: str, start: int, end: int, width: int = CONTEXT_WIDTH) -> str:
    return text[max(0, start - width): end + width].replace("\n", " ")


def scan(rows: list[dict], mirrors: list[Path]) -> list[dict]:
    """Return a list of hit dicts: id, severity, kind, doc, line, context."""
    hits = []
    for row in rows:
        pat = row["compiled"]
        if pat is None:
            continue
        for path in mirrors:
            if path.stem in row["allow_docs"]:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for m in pat.finditer(text):
                if row["allow_context"] is not None:
                    before = text[max(0, m.start() - ALLOW_CONTEXT_WIDTH): m.start()]
                    if row["allow_context"].search(before):
                        continue
                line = text.count("\n", 0, m.start()) + 1
                hits.append({
                    "id": row["id"],
                    "severity": row["severity"],
                    "kind": row["kind"],
                    "doc": path.name,
                    "line": line,
                    "context": _context(text, m.start(), m.end()).strip(),
                })
    return hits


def selftest() -> bool:
    import tempfile

    synth_rows = [
        {"id": "T-PHRASE", "pattern_src": r"residence time",
         "compiled": re.compile(r"residence time", re.IGNORECASE), "kind": "phrase",
         "reason": "t", "allow_docs": [], "allow_context": re.compile(r"\bnot\b.{0,20}$", re.I),
         "severity": "gate"},
        {"id": "T-NUMBER", "pattern_src": r"\b117\s+measuring points\b",
         "compiled": re.compile(r"\b117\s+measuring points\b", re.IGNORECASE), "kind": "number",
         "reason": "t", "allow_docs": [], "allow_context": None, "severity": "gate"},
        {"id": "T-CHAR", "pattern_src": " ",
         "compiled": re.compile(" "), "kind": "char",
         "reason": "t", "allow_docs": [], "allow_context": None, "severity": "gate"},
        {"id": "T-DATE", "pattern_src": r"\b20\d{2}-\d{2}-\d{2}\b",
         "compiled": re.compile(r"\b20\d{2}-\d{2}-\d{2}\b", re.IGNORECASE), "kind": "date",
         "reason": "t", "allow_docs": [],
         "allow_context": re.compile(r"frame|event", re.IGNORECASE), "severity": "advisory"},
        {"id": "T-ALLOWDOC", "pattern_src": r"\bretired figure\b",
         "compiled": re.compile(r"\bretired figure\b", re.IGNORECASE), "kind": "phrase",
         "reason": "t", "allow_docs": ["fixture"], "allow_context": None, "severity": "gate"},
    ]

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "fixture.md"
        p.write_text(
            "Sentence A: tau is not a residence time in this passage (D-010).\n"
            # T-PHRASE: admitted -- "not" sits just before the hit.
            "Sentence B: incorrectly, the aquifer's residence time is tau here.\n"
            # T-PHRASE: real hit -- no "not" nearby.
            "Sentence C: the network comprises 117 measuring points at Newborough.\n"
            # T-NUMBER: real hit.
            "Sentence D: a gap here uses the retired em space.\n"
            # T-CHAR: real hit.
            "Sentence E: the frame dated 2020-03-31 shows the felled compartment; "
            "a later note cites 2021-06-01 with no marker.\n"
            # T-DATE: first date admitted ("frame" precedes it); second date is a
            # real (advisory) hit -- no frame/event word precedes it.
            "Sentence F: this document carries a retired figure on purpose.\n",
            # T-ALLOWDOC: fully admitted via allow_docs (doc stem "fixture").
            encoding="utf-8",
        )
        hits = scan(synth_rows, [p])

    by_id = {}
    for h in hits:
        by_id.setdefault(h["id"], []).append(h)

    ok = True
    checks = [
        (len(by_id.get("T-PHRASE", [])) == 1, "T-PHRASE should have exactly 1 hit"),
        (len(by_id.get("T-NUMBER", [])) == 1, "T-NUMBER should have exactly 1 hit"),
        (len(by_id.get("T-CHAR", [])) == 1, "T-CHAR should have exactly 1 hit"),
        (len(by_id.get("T-DATE", [])) == 1, "T-DATE should have exactly 1 hit (one admitted)"),
        ("T-ALLOWDOC" not in by_id, "T-ALLOWDOC should be fully admitted via allow_docs"),
    ]
    for cond, msg in checks:
        if not cond:
            ok = False
            print(f"  selftest FAIL: {msg}")
    if not ok:
        print(f"  hits by id: { {k: len(v) for k, v in by_id.items()} }")

    # CSV-load self-check: the real CSV must load with zero load faults and
    # zero stale allow_docs against the real corpus.
    rows, load_faults = load_rows()
    if load_faults:
        ok = False
        print(f"  selftest FAIL: real CSV has load faults: {load_faults}")
    stale = check_stale_allow_docs(rows, find_mirrors())
    if stale:
        ok = False
        print(f"  selftest FAIL: real CSV has stale allow_docs: {stale}")

    return ok


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        ok = selftest()
        print("  retired_phrase_lint selftest: " + ("OK" if ok else "FAIL"))
        return 0 if ok else 1

    rows, load_faults = load_rows()
    mirrors = find_mirrors()
    stale_faults = check_stale_allow_docs(rows, mirrors)

    rc = 0
    for f in load_faults + stale_faults:
        print(f"  FAIL {f}")
        rc = 1

    hits = scan(rows, mirrors)
    hits.sort(key=lambda h: (h["doc"], h["line"], h["id"]))

    gate_hits = [h for h in hits if h["severity"] == "gate"]
    advisory_hits = [h for h in hits if h["severity"] == "advisory"]

    for h in gate_hits:
        print(f"  FAIL {h['doc']}:{h['line']}: [{h['id']}] …{h['context']}…")
        rc = 1
    if not args.quiet:
        for h in advisory_hits:
            print(f"  NOTE {h['doc']}:{h['line']}: [{h['id']}] …{h['context']}…")

    by_kind: dict[str, int] = {}
    for h in hits:
        by_kind[h["kind"]] = by_kind.get(h["kind"], 0) + 1
    kind_summary = ", ".join(f"{k}={v}" for k, v in sorted(by_kind.items())) or "none"

    if rc:
        print(f"  retired_phrase_lint: {len(gate_hits)} gate hit(s), "
              f"{len(advisory_hits)} advisory hit(s), {len(load_faults)} CSV load fault(s), "
              f"{len(stale_faults)} stale allow_docs row(s) — by kind: {kind_summary}")
    elif not args.quiet or advisory_hits:
        print(f"  retired_phrase_lint: {len(rows)} row(s) scanned across {len(mirrors)} "
              f"mirror(s); 0 gate hits, {len(advisory_hits)} advisory hit(s) — by kind: "
              f"{kind_summary}")

    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
