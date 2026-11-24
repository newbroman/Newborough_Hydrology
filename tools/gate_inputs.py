#!/usr/bin/env python3
"""gate_inputs.py — a gate declares what it reads, and may not pass having read nothing (D-327, T-204).

In a documents-free clone (a cloud session without the Drive secret, which CLAUDE.md §4g blesses) several gates
read OK on zero subjects — "all 0 table(s) trace to a committed output" — and two crashed outright. D-327: a gate
reports one of three things:

    OK on a stated number of subjects (at least its floor)
    SKIP (inputs absent by design), naming what is missing        exit 0, and says so
    FAIL                                                            exit 1

Examining zero subjects is a FAIL, not an OK. No gate raises because an input it never declared is absent.

    from gate_inputs import declare_inputs
    inp = declare_inputs("table_provenance_lint", chapters="report_edits/odt/report*.odt")
    if inp.absent:
        return inp.skip()              # prints the SKIP line, returns 0
    ... examine n subjects ...
    bad = inp.floor_fault(n, what="table(s)")   # None, or the FAIL line already printed
    if bad: return bad

A label may name several paths or globs (a list); it is present when any one matches. `paper_refs.py` is the
pattern this generalises.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-11-24. New (T-204, D-327).

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent


class Inputs:
    def __init__(self, gate: str, spec: dict[str, list[str]]):
        self.gate, self.spec = gate, spec
        self.absent = [label for label, pats in spec.items()
                       if not any(_present(p) for p in pats)]

    def skip(self) -> int:
        what = "; ".join(f"{label} ({', '.join(self.spec[label])})" for label in self.absent)
        print(f"{self.gate}: SKIP (inputs absent by design) — no {what}. Nothing was checked.")
        return 0

    def floor_fault(self, n: int, what: str = "subject(s)", floor: int = 1) -> int | None:
        if n >= floor:
            return None
        print(f"{self.gate}: FAIL — examined {n} {what}, below the floor of {floor}: its inputs are present, "
              f"so a pass on nothing is not an OK (D-327)")
        return 1


def _present(pattern: str) -> bool:
    if any(c in pattern for c in "*?["):
        return any(True for _ in REPO.glob(pattern))
    return (REPO / pattern).exists()


def declare_inputs(gate: str, **inputs) -> Inputs:
    return Inputs(gate, {k: ([v] if isinstance(v, str) else list(v)) for k, v in inputs.items()})


def selftest() -> int:
    a = declare_inputs("t", here="tools/gate_inputs.py", glob="tools/*.py")
    b = declare_inputs("t", gone="no/such/file.odt", alt=["no/such/*.odt", "tools/gate_inputs.py"])
    ok = (not a.absent and b.absent == ["gone"] and a.floor_fault(0) == 1 and a.floor_fault(3) is None
          and a.floor_fault(2, floor=5) == 1)
    print(f"  gate_inputs --selftest: {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 0)
