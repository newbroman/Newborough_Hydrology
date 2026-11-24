#!/usr/bin/env python3
"""witness_lint.py — does every gate name its witness? (D-325, T-202)

D-325: a gate must compare two things one actor cannot both produce, and must NAME ITS WITNESS. Six are
admissible: the committed content, origin, a pinned snapshot, a recorded content hash, an exhaustive proof, and a
measured quantity with a target. A check that names none of these is a report: it prints and does not gate.

tools/gate_witness.csv carries one row per `gated` rule of tools/rule_gate_matrix.csv: its witness (one of the six,
or `none`), the tool judged, and one sentence of evidence with file:line. First populated 2026-11-24 by reading
each gate's source as check_all invokes it.

    FAIL   a gated rule with no row, a row with a token outside the seven, or a row for a rule no longer gated
    LIST   every `none`: by D-325 these report rather than gate. Each is listed with its evidence; demoting one in
           check_all.sh is a ruling on that classification, made by Martin, not by this lint (T-202 note)

    python3 tools/witness_lint.py
    python3 tools/witness_lint.py --selftest
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-11-24. New (T-202, D-325).

import csv
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
MATRIX = REPO / "tools/rule_gate_matrix.csv"
WITNESS = REPO / "tools/gate_witness.csv"
ADMISSIBLE = ("committed", "origin", "snapshot", "hash", "proof", "measured")


def verdict(matrix: list[dict], witness: list[dict]) -> tuple[list[str], list[dict]]:
    gated = {r["id"] for r in matrix if r.get("enforcement", "").strip() == "gated"}
    by = {r["id"]: r for r in witness}
    faults = [f"{i}: gated in the matrix, and names no witness row" for i in sorted(gated - set(by))]
    faults += [f"{i}: has a witness row but is not gated in the matrix" for i in sorted(set(by) - gated)]
    faults += [f"{i}: witness {r['witness']!r} is not one of {ADMISSIBLE + ('none',)}" for i, r in sorted(by.items())
               if r["witness"] not in ADMISSIBLE + ("none",)]
    return faults, [r for i, r in sorted(by.items()) if i in gated and r["witness"] == "none"]


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        m = [{"id": "R1", "enforcement": "gated"}, {"id": "R2", "enforcement": "gated"}, {"id": "R3", "enforcement": "partial"}]
        w = [{"id": "R1", "witness": "hash"}, {"id": "R3", "witness": "proof"}, {"id": "R2", "witness": "none"}]
        f, n = verdict(m, w)
        ok = (len(f) == 1 and "R3" in f[0] and [r["id"] for r in n] == ["R2"]
              and len(verdict(m, [{"id": "R1", "witness": "vibes"}])[0]) == 2)
        print(f"  witness_lint --selftest: {'OK' if ok else 'FAIL'}")
        return 0 if ok else 1
    rd = lambda p: list(csv.DictReader(open(p, encoding="utf-8", newline="")))
    faults, none = verdict(rd(MATRIX), rd(WITNESS))
    for f in faults:
        print(f"  FAIL  {f}")
    if none:
        print(f"  {len(none)} gated rule(s) name NO witness — by D-325 a report, not a gate (demotion awaits a ruling):")
        for r in none:
            print(f"    {r['id']:4s} {r['tool']:28s} {r['evidence'][:110]}")
    n = sum(1 for r in rd(WITNESS))
    print(f"witness_lint: {'FAIL' if faults else 'OK'} — {n} gated rule(s), {n - len(none)} with a witness, {len(none)} without")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
