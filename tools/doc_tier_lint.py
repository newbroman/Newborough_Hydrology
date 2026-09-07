#!/usr/bin/env python3
"""
doc_tier_lint — is the document-phase register complete and self-consistent? (D-144)

Checks, all gating:
  1. Every ODT/ODM family on disk (docs/**, report_edits/odt) has a doc_tier.csv row,
     and every row names a family that exists. An unregistered family is one
     odt_edit would refuse to write — so this fails BEFORE a session meets that.
  2. `current` agrees with the phase: a family is `live` iff its phase_live equals
     the header's phase. (A family live out of phase is a decision, and needs the
     header changed with a D-entry, not a cell changed by hand.)
  3. Every `set_by` and every logged `reason` that is a D-number exists in the
     decision log; every logged reason is a valid reason (D-number, changelog id,
     or exempt tool).
  4. Header carries phase= and set_by=.

Usage:
    python3 tools/doc_tier_lint.py             # report, exit 1 on any fault
    python3 tools/doc_tier_lint.py --selftest  # exercise the detectors
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-07. First issue (D-144).

import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from doc_tier import (REGISTER, LOG, STATES, family, read_register,   # noqa: E402
                      reason_is_valid)

ODT_GLOBS = ("docs/**/*.odt", "docs/**/*.odm", "report_edits/odt/*.odt", "report_edits/odt/*.odm")


def families_on_disk() -> set[str]:
    fams = set()
    for g in ODT_GLOBS:
        for p in REPO.glob(g):
            if p.name.startswith((".", "~")) or "_to_delete" in p.parts:
                continue
            f = family(p)
            if f:
                fams.add(f)
    return fams


def decision_ids() -> set[str]:
    try:
        from context_for import parse_entries
        return {e["id"] for e in parse_entries()}
    except Exception as exc:                       # the lint must still run without it
        print(f"  warn  could not parse the decision log ({exc}); D-number checks skipped")
        return set()


def evaluate(meta: dict, rows: dict[str, dict], on_disk: set[str],
             dids: set[str] | None, log_rows: list[dict]) -> list[str]:
    faults = []
    phase = meta.get("phase")
    if not phase:
        faults.append("header comment lacks phase=")
    if not meta.get("set_by"):
        faults.append("header comment lacks set_by=")
    for f in sorted(on_disk - set(rows)):
        faults.append(f"no doc_tier.csv row for family {f!r} (odt_edit would refuse to write it)")
    for f in sorted(set(rows) - on_disk):
        faults.append(f"row {f!r} names a family with no ODT on disk")
    for f, r in rows.items():
        cur = r.get("current")
        if cur not in STATES:
            faults.append(f"{f}: current={cur!r} is not one of {STATES}")
            continue
        want = "live" if (phase and r.get("phase_live") == phase) else "frozen"
        if cur != want:
            faults.append(f"{f}: current={cur} but phase={phase} and phase_live={r.get('phase_live')} "
                          f"imply {want} — change the phase (with a D-entry), not the cell")
        sb = r.get("set_by", "")
        if not reason_is_valid(sb):
            faults.append(f"{f}: set_by={sb!r} is not a D-number or changelog id")
        elif dids is not None and sb.startswith("D-") and sb not in dids:
            faults.append(f"{f}: set_by {sb} is not in the decision log")
    for i, lr in enumerate(log_rows, 1):
        rs = lr.get("reason", "")
        if not reason_is_valid(rs):
            faults.append(f"doc_tier_log row {i}: reason {rs!r} invalid")
        elif dids is not None and rs.startswith("D-") and rs not in dids:
            faults.append(f"doc_tier_log row {i}: {rs} is not in the decision log")
        if lr.get("family") not in rows:
            faults.append(f"doc_tier_log row {i}: family {lr.get('family')!r} has no register row")
    return faults


def read_log() -> list[dict]:
    if not LOG.is_file():
        return []
    with LOG.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def selftest() -> int:
    meta = {"phase": "1", "set_by": "D-144"}
    rows = {"report": {"family": "report", "phase_live": "1", "current": "live", "set_by": "D-144"},
            "Paper1": {"family": "Paper1", "phase_live": "2", "current": "frozen", "set_by": "D-144"}}
    disk = {"report", "Paper1"}
    ok = evaluate(meta, rows, disk, {"D-144"}, []) == []
    bad = []
    if not ok:
        bad.append("clean case reported faults")
    if not evaluate(meta, rows, disk | {"Supplementary_Material"}, {"D-144"}, []):
        bad.append("missing row not detected")
    r2 = {**rows, "Paper1": {**rows["Paper1"], "current": "live"}}
    if not any("imply frozen" in f for f in evaluate(meta, r2, disk, {"D-144"}, [])):
        bad.append("out-of-phase live not detected")
    if not evaluate(meta, rows, disk, {"D-144"}, [{"family": "Paper1", "reason": "because"}]):
        bad.append("invalid log reason not detected")
    if not evaluate(meta, rows, disk, {"D-144"}, [{"family": "Paper1", "reason": "D-999"}]):
        bad.append("unknown D-number in log not detected")
    if family("report10.odt") != "report" or family("Paper1_v1_38.odt") != "Paper1" \
            or family("x.md") is not None:
        bad.append("family() derivation")
    if bad:
        print("doc_tier_lint --selftest: FAIL")
        for b in bad:
            print(f"    - {b}")
        return 1
    print("doc_tier_lint --selftest: OK")
    return 0


def main(argv) -> int:
    if "--selftest" in argv:
        return selftest()
    if not REGISTER.is_file():
        print(f"doc_tier_lint: FAULT — {REGISTER.relative_to(REPO)} missing")
        return 1
    meta, rows = read_register()
    faults = evaluate(meta, rows, families_on_disk(), decision_ids(), read_log())
    live = [f for f, r in rows.items() if r.get("current") == "live"]
    print(f"  phase {meta.get('phase')} (set by {meta.get('set_by')}): "
          f"live = {', '.join(live) or 'none'}; {len(rows) - len(live)} frozen; "
          f"{len(read_log())} logged frozen-document write(s)")
    if faults:
        print("doc_tier_lint: FAULT")
        for f in faults:
            print(f"    - {f}")
        return 1
    print("doc_tier_lint: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
