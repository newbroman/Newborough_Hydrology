#!/usr/bin/env python3
"""
ledger_lint.py — does SCRIPT_LEDGER.md still describe the code?

WHAT GOES WRONG WITHOUT IT

  `notes/ledgers/SCRIPT_LEDGER.md` calls itself "the anti-drift spine — read it to know
  the current state without replaying the changelog history", and states its own
  maintenance rule: *every script change updates its row here*. Nothing enforced
  that rule, and on 2026-08-24 the measurement was:

      29 of 67 rows carried a stale version
      2 scripts had no row at all (10n, 39)
      the header still cited HEAD 30aed9b, ten days old

  `25_coastal_gradient` read 1.6.2 against a live 1.17.0. A reader following the
  ledger's own instruction — read this instead of the changelog — would have been
  eleven minor versions out on the script the coastal chapter rests on.

  This is the third record in this project to rot the same way. `citation_index`
  did it until `cite_check`; the decision log did it until `decision_lint`. The
  pattern is not carelessness, it is that A RECORD NOTHING READS IS A RECORD THAT
  ROTS, and the remedy each time was a check rather than a resolution to try
  harder.

WHAT IT CHECKS, AND WHAT IT REFUSES TO CHECK

  GATE — structural faults, which are unambiguous and cheap to fix:
    * a script in src/ with no row (it is invisible to anyone reading the ledger)
    * a row naming a script that no longer exists (it describes nothing)

  ADVISORY — version drift. Printed, counted, not gated. Twenty-nine stale rows
  is a maintenance backlog, and a gate that fails from the day it lands is a gate
  someone switches off within the week. The same reasoning check_all already
  applies to pipeline_lint's literal check and to export_lag.

  NOT CHECKED — Consumes, Emits and Cited. Those need a human to read the script,
  and a tool that pretended to verify them would produce exactly the false
  assurance the ledger already suffers from. `--fix-versions` therefore bumps the
  version and sets Status to **DRIFT?**, the ledger's own token for "moved, not
  re-reconciled". It never writes **OK**: only a person who has re-read the
  script's inputs and outputs may do that.

Usage:
    python3 tools/ledger_lint.py                 # report
    python3 tools/ledger_lint.py --quiet         # gate faults only
    python3 tools/ledger_lint.py --fix-versions  # bump Ver, mark Status DRIFT?
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) — 2026-09-01. Adds the
#   DOCSTRING VERSION check. Three modules carried a `__version__ :` line inside
#   their module docstring that had drifted from the real assignment, because the
#   bump convention updates one copy and not the other. Nothing downstream was
#   broken — every tool here reads the assignment — but on 2026-09-01 the stale
#   docstring line in 41_canopy_cover.py was read as the live version and a sound
#   ledger row was reported as a defect on the strength of it. A file that states
#   a version it does not have is a trap for the next reader, human or not.
#
# v1.0.0  # Hollingham (2026) — 2026-08-25.

import argparse
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "notes/ledgers/SCRIPT_LEDGER.md"
SRC = REPO / "src"

# The ledger declares its own exemptions, in prose:
#
#   *(Not rows: `gen_grid_lay.py`, `run_09_scraping.py`, `run_10_clearfell.py`
#     — utility/orchestration.)*
#
# They are READ FROM THE LEDGER rather than copied here. A hard-coded list would
# be a second place the same fact lives, and this project has spent the day
# fixing the consequences of exactly that — a donor pool duplicated beside the
# analysis that reads it, a decision log with two numbering schemes, a mirror
# generator superseded but not retired. The ledger says what it does not cover;
# this tool believes it.
_EXEMPT = re.compile(r"Not rows:(.*?)—", re.S)

# The top-level orchestrator is the one exemption the ledger does not state,
# because it lives outside src/ and never appeared in the scan that built it.
ALWAYS_EXEMPT = {"run_analysis.py"}


def declared_exemptions(text: str) -> set[str]:
    m = _EXEMPT.search(text)
    if not m:
        return set()
    return set(re.findall(r"`([^`]+\.py)`", m.group(1)))

_VER = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.M)


def live_version(script: str) -> str | None:
    p = SRC / script
    if not p.exists():
        return None
    m = _VER.search(p.read_text(encoding="utf-8", errors="ignore"))
    return m.group(1) if m else None


# A version line inside a module docstring, e.g. `__version__ : 2.0.0`. Not an
# assignment — the colon form is prose, and Python never reads it — which is
# exactly why it drifts.
_DOC_VER = re.compile(r'^__version__\s*:\s*([0-9][0-9A-Za-z._-]*)\s*$', re.M)


def docstring_version_drift() -> list[tuple[str, str, str]]:
    """Files whose docstring version line disagrees with the assignment.

    Scans src/ recursively, not just the ledger's rows: two of the three known
    cases were in src/utils/, which has no ledger row and would otherwise never
    be checked.
    """
    out = []
    for p in sorted(SRC.rglob("*.py")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        md = _DOC_VER.search(text)
        if not md:
            continue
        ma = _VER.search(text)
        if not ma:
            continue
        if md.group(1) != ma.group(1):
            out.append((str(p.relative_to(REPO)), md.group(1), ma.group(1)))
    return out


def rows(text: str) -> list[dict]:
    out = []
    for i, line in enumerate(text.split("\n")):
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 8 or cells[1] in ("Script", "--------"):
            continue
        if not cells[1].endswith(".py"):
            continue
        out.append({"line": i, "id": cells[0], "script": cells[1],
                    "ver": cells[2], "status": cells[-1], "cells": cells})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--fix-versions", action="store_true")
    args = ap.parse_args()

    if not LEDGER.exists():
        print(f"  SKIP  {LEDGER.name} not in this checkout")
        return 0

    text = LEDGER.read_text(encoding="utf-8")
    rs = rows(text)
    listed = {r["script"] for r in rs}
    exempt = declared_exemptions(text) | ALWAYS_EXEMPT
    on_disk = {p.name for p in SRC.glob("*.py")} - exempt

    missing = sorted(on_disk - listed)
    orphan = sorted(s for s in listed if not (SRC / s).exists())

    drift = []
    for r in rs:
        live = live_version(r["script"])
        if live is None:
            continue
        # A few rows record a supersession inline, e.g. "1.3.0 (live 1.4.0)".
        # Compare against the first version token only.
        recorded = r["ver"].split()[0].strip("`*")
        if recorded != live:
            drift.append((r, recorded, live))

    fail = 0
    if missing:
        fail = 1
        print(f"  FAIL  {len(missing)} script(s) in src/ with no ledger row:")
        for s in missing:
            print(f"          {s}")
    if orphan:
        fail = 1
        print(f"  FAIL  {len(orphan)} row(s) naming a script that no longer exists:")
        for s in orphan:
            print(f"          {s}")

    docdrift = docstring_version_drift()
    if docdrift:
        fail = 1
        print(f"  FAIL  {len(docdrift)} module(s) whose docstring states a "
              f"version the file does not have:")
        for rel, doc, live in docdrift:
            print(f"          {rel:<40} docstring {doc:<10} assignment {live}")
        print("          The assignment is authoritative and every tool reads it;")
        print("          the docstring line is prose that the bump convention")
        print("          forgets. Correct the docstring, not the assignment.")
    elif not args.quiet:
        print("  docstring version lines agree with their assignments")

    if not args.quiet or drift:
        print(f"  {len(drift)} row(s) with a stale version "
              f"(advisory — the ledger's own maintenance backlog)")
    if drift and not args.quiet:
        for r, rec, live in drift:
            print(f"      {r['script']:<38} ledger {rec:<10} live {live}")

    if args.fix_versions and drift:
        lines = text.split("\n")
        for r, rec, live in drift:
            cells = r["cells"][:]
            cells[2] = live
            # Never write OK. A version bump says the code moved; it says
            # nothing about whether Consumes/Emits still describe it.
            if not cells[-1].startswith("**DRIFT"):
                cells[-1] = "**DRIFT?**"
            lines[r["line"]] = "| " + " | ".join(cells) + " |"
        LEDGER.write_text("\n".join(lines), encoding="utf-8")
        print(f"\n  bumped {len(drift)} version(s); each row marked **DRIFT?** —")
        print(f"  re-read the script's Consumes/Emits before setting any to OK.")

    if not fail and not args.quiet:
        print(f"  ledger_lint: {len(rs)} rows, every script listed, no orphans "
              f"({len(exempt)} declared exemption(s))")
    if fail:
        print("ledger_lint: FAIL")
    elif args.quiet:
        print("ledger_lint: OK")
    return fail


if __name__ == "__main__":
    raise SystemExit(main())
