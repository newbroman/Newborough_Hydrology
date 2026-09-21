#!/usr/bin/env python3
"""
xref_lint.py
============
The report does not send its reader to the Methods Supplement.

Why this exists.

  CLAUDE.md has carried the rule since the Supplement existed: "Do not send a
  reader to the Methods Supplement. Say the thing, or name the script that does
  it. A cross-reference is a promise that the other document says what you
  think it says, and this corpus has repeatedly not. Applies to the Supplement
  referring to itself by chapter as well." Nothing checked it. On 2026-09-21 two
  edit batches (reasons 21e and 21f) added six such pointers to report8, report9
  and report10 in one morning, each in good faith, and the rule was found by the
  author reading the proof copy, not by a gate (Martin: "now I am worried we
  dont have adequate checks to ensure the project rules are followed"). A rule
  that lives only in a prose file is a rule that a fresh session re-breaks.

What it flags.

  In every report chapter mirror (report_edits/text/report*.md) — the text a
  reader receives — any of:
    "Methods Supplement"            the document named as a destination
    "Supplement §…" / "MS S.…"      a chapter of it
    "§F.n" / "(F.n)"                its appendix-F registers
  A bibliographic citation of the Supplement as a whole (report15's reference
  entry, the sentence that says a supplement accompanies the report) is not a
  destination and is allowlisted. The Supplementary Material (Notes S1–S11) is
  a different document, holds results rather than methods, and is not covered
  by the rule; it is not flagged.

  The Supplement's own self-references by chapter ("§S.15", "Section S.18")
  are counted and reported — the rule covers them — but do not fail the gate
  until Martin says they should: there are over a hundred of them and each is
  an editorial call.

Allowlist.

  tools/xref_allow.csv: doc, fragment, note. A row admits one occurrence of
  `fragment` in `doc`. Every row is a pointer the author has chosen to keep,
  with the reason; adding a row to quiet the lint is the failure this file
  exists to prevent. Rows that no longer match anything are reported, so the
  file cannot silently outlive the text it excuses.

Usage:
    python3 tools/xref_lint.py            # report, non-zero exit on a fault
    python3 tools/xref_lint.py --quiet    # one line unless something fails
    python3 tools/xref_lint.py --selftest
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-21. First gate for the
#   CLAUDE.md "do not send a reader to the Methods Supplement" rule.

REPO = Path(__file__).resolve().parents[1]
MIRRORS = sorted(REPO.glob("report_edits/text/report*.md"))
MS_MIRROR = REPO / "docs/report/text/Newborough_Methods_Supplement.md"
ALLOW = REPO / "tools/xref_allow.csv"

# One occurrence per match; the fragment reported is the match plus context.
PATTERNS = [
    re.compile(r"Methods Supplement"),
    re.compile(r"\bSupplement\s*§"),
    re.compile(r"\bMS\s+§?S\.\d"),
    re.compile(r"[(§]\s*F\.\d+\b"),
]
MS_SELF = re.compile(r"(?:§|Section)\s*S\.\d+(?:\.\d+)*")


def _allow() -> list[dict]:
    if not ALLOW.exists():
        return []
    with ALLOW.open(newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if r.get("doc")]


def _context(text: str, start: int, end: int, width: int = 60) -> str:
    return text[max(0, start - width): end + width].replace("\n", " ")


def scan(mirrors=MIRRORS, allow_rows=None):
    """Return (faults, used_allow) where faults is a list of (doc, line, context)."""
    allow_rows = _allow() if allow_rows is None else allow_rows
    used = [False] * len(allow_rows)
    faults = []
    for path in mirrors:
        doc = path.stem
        text = path.read_text(encoding="utf-8")
        spans = sorted((m.start(), m.end()) for pat in PATTERNS for m in pat.finditer(text))
        merged: list[list[int]] = []          # one fault per pointer, however many
        for s, e in spans:                    # patterns it satisfies
            if merged and s <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], e)
            else:
                merged.append([s, e])
        for s, e in merged:
            ctx = _context(text, s, e)
            line = text.count("\n", 0, s) + 1
            ok = False
            for i, row in enumerate(allow_rows):
                if row["doc"] == doc and row["fragment"] in ctx and not used[i]:
                    used[i] = True
                    ok = True
                    break
            if not ok:
                faults.append((doc, line, ctx.strip()))
    return faults, used


def ms_self_count() -> int:
    if not MS_MIRROR.exists():
        return -1
    return len(MS_SELF.findall(MS_MIRROR.read_text(encoding="utf-8")))


def selftest() -> bool:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "report99.md"
        p.write_text("Fine sentence (Script 31). Bad one (Methods Supplement S.22). "
                     "Register (F.6). Cited: MS S.16 here. Supplement §S.20.6 too.\n"
                     "Allowed: the Methods Supplement accompanies this report.",
                     encoding="utf-8")
        allow = [{"doc": "report99", "fragment": "accompanies this report", "note": "t"}]
        faults, used = scan([p], allow)
        ok = len(faults) == 4 and used == [True]
        if not ok:
            print(f"  selftest FAIL: {len(faults)} fault(s) (want 4), used={used}")
            for f in faults:
                print("   ", f)
        return ok


def main(argv) -> int:
    quiet = "--quiet" in argv
    if "--selftest" in argv:
        ok = selftest()
        print("  xref_lint selftest: " + ("OK" if ok else "FAIL"))
        return 0 if ok else 1
    allow_rows = _allow()
    faults, used = scan(allow_rows=allow_rows)
    stale = [r for r, u in zip(allow_rows, used) if not u]
    n_ms = ms_self_count()
    rc = 0
    for doc, line, ctx in faults:
        print(f"  FAIL {doc}.md:{line}: …{ctx}…")
        rc = 1
    for r in stale:
        print(f"  FAIL xref_allow.csv row matches nothing: {r['doc']} / {r['fragment']!r}")
        rc = 1
    if rc:
        print(f"  xref_lint: {len(faults)} Methods Supplement pointer(s) in the report "
              f"chapters, {len(stale)} stale allowlist row(s) — say the thing or name the script")
    elif not quiet or n_ms > 0:
        print(f"  xref_lint: report chapters send no reader to the Methods Supplement "
              f"({len(allow_rows)} allowlisted); the Supplement refers to itself by chapter "
              f"{n_ms} time(s) (advisory)")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
