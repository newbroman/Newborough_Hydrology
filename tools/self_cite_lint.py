#!/usr/bin/env python3
"""
self_cite_lint — does every paper label the author's own 2026 works the same way?

Why this exists (2026-10-06, changelog 2026-10-06f).
  The three papers cite five of the author's own 2026 works, and each reference list lettered
  them for itself: "Hollingham, 2026a" was the technical report in Paper 1 and Paper 1 in Papers
  2 and M, and Paper 2 had used its one "2026a" for both Paper 1 and the report (26 of 33 cites
  were the report). Martin, 2026-10-06: one fixed letter per work, in every paper.

  tools/self_citations.csv is the register: label, work, title. For each paper mirror below:
    1. every in-text "Hollingham, 2026x" / "Hollingham (2026x" has a reference entry in the same
       document beginning "Hollingham, M." with that label;
    2. every such entry carries the register title for its label (case- and punctuation-blind);
    3. every entry is cited at least once in the text. The Paper 1 SI has no reference list of its
       own (it uses Paper 1's), so for it only check 4 applies;
    4. no unlettered "Hollingham, 2026" citation remains (an unlettered cite cannot be resolved).
  Documents that cite only one 2026 work (the report, the Supplements, the manuals) keep a plain
  "2026" and are not checked.

Usage:  python3 tools/self_cite_lint.py [--selftest]
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-10-06. First issue.

import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTER = REPO / "tools" / "self_citations.csv"
DOCS = ["docs/papers/paper_1/text/Paper1.md",
        "docs/papers/paper_1/text/PAPER1_SI_methods.md",
        "docs/papers/paper_2/text/Hollingham_2026_Paper2_amended.md",
        "docs/papers/paper_M/text/PaperM.md"]
CITE_RE = re.compile(r"Hollingham(?:,|\s*\()\s*(2026[a-z]?)\b")
ENTRY_RE = re.compile(r"^(?:>\s*)?Hollingham,\s*M\.,?\s*\(?(2026[a-z]?)\)?[.,]?\s*(.*)$", re.M)


def squash(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower().replace("\\", ""))


def register() -> dict[str, str]:
    with REGISTER.open(encoding="utf-8") as fh:
        return {r["label"]: r["title"] for r in csv.DictReader(fh)}


def evaluate(name: str, text: str, reg: dict[str, str]) -> list[str]:
    faults = []
    entries = {}
    spans = []
    for m in ENTRY_RE.finditer(text):
        entries.setdefault(m.group(1), m.group(2))
        spans.append((m.start(), m.end()))
    def in_entry(pos):
        return any(a <= pos < b for a, b in spans)
    cited = set()
    for m in CITE_RE.finditer(text):
        if in_entry(m.start()):
            continue
        lab = m.group(1)
        if lab == "2026":
            faults.append(f"{name}: unlettered 'Hollingham, 2026' citation at offset {m.start()}")
            continue
        cited.add(lab)
        if lab not in entries and "SI_methods" not in name:   # the SI uses Paper 1's list
            faults.append(f"{name}: {lab} cited but has no reference entry")
    for lab, rest in entries.items():
        if lab not in reg:
            faults.append(f"{name}: entry {lab} is not in self_citations.csv")
            continue
        if squash(reg[lab]) not in squash(rest):
            faults.append(f"{name}: entry {lab} does not carry the register title ({reg[lab][:50]}…)")
        if lab not in cited and "SI_methods" not in name:
            faults.append(f"{name}: entry {lab} is never cited")
    return faults


def selftest() -> int:
    reg = {"2026a": "Paper One Title", "2026d": "The Report"}
    good = "Text (Hollingham, 2026a) and (Hollingham, 2026d).\n\nHollingham, M., 2026a. Paper One Title. X.\n\nHollingham, M., 2026d. The Report. Y.\n"
    bad = []
    if evaluate("t", good, reg):
        bad.append("clean document faulted")
    if not evaluate("t", good.replace("2026d. The Report", "2026d. Other"), reg):
        bad.append("wrong title not detected")
    if not evaluate("t", good.replace("(Hollingham, 2026d)", "(Hollingham, 2026)"), reg):
        bad.append("unlettered cite not detected")
    if not evaluate("t", good + "\n(Hollingham, 2026c)", reg):
        bad.append("cite without entry not detected")
    print("self_cite_lint selftest:", "OK" if not bad else "FAIL " + "; ".join(bad))
    return 1 if bad else 0


def main(argv) -> int:
    if "--selftest" in argv:
        return selftest()
    reg = register()
    faults = []
    for d in DOCS:
        p = REPO / d
        if not p.is_file():
            faults.append(f"{d}: mirror missing")
            continue
        faults += evaluate(p.name, p.read_text(encoding="utf-8"), reg)
    for f in faults:
        print("  FAIL", f)
    print("self_cite_lint:", "OK" if not faults else f"FAIL — {len(faults)} fault(s)",
          f"({len(DOCS)} papers, {len(reg)} registered works)")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
