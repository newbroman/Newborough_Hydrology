#!/usr/bin/env python3
"""
deferred_report — the decisions that were deliberately NOT taken, and are still
waiting on a person.

WHY

  This project defers well and remembers badly. A session that reaches a
  question it should not answer alone writes the deferral into the decision log
  and moves on — "Not decided here", "pending Martin", "deliberately not built",
  "Not yet written" — and that sentence is then the only record that anything is
  owed. It is prose in a 5,000-line file. Nothing surfaces it.

  Three registers already exist and none of them catches this. tools/task_lint
  tracks T-numbered jobs, but a deferral only becomes a T-number if someone
  remembers to add one. The work register tracks W rows, but its status cell is
  hand-maintained and drifts (on 2026-08-29 an audit found 18 of 23 "open" rows
  had in fact been discharged). DECISION_INDEX lists every decision, discharged
  or not, which is not the same question.

  So this reads the decision log for deferral markers and reports what it finds,
  cross-referenced against the two registers that could be tracking it. The
  output belongs in the daily view: what is waiting on ME, as opposed to what is
  waiting on the pipeline.

REPORTED, NOT GATED. A deferral is the project working correctly — it is a
session declining to make someone else's call. Failing the build on an
outstanding decision would punish exactly the behaviour that keeps the record
honest. What must not happen is the deferral going quiet, and that is what this
prevents.

WHAT IT CANNOT SEE

  * A deferral phrased in words not in MARKERS. The list is hand-maintained and
    will lag the prose, which is why the marker that matched is printed beside
    every hit: a reader can see WHICH form was caught and infer which were not.
  * Whether a deferral has since been discharged — unless the entry says so. A
    decision that carried a deferral and has since had it answered should gain

        - **Deferral discharged:** <what settled it, and when>

    which retires it from this report. That is deliberately an explicit act: a
    tool that guessed at discharge would quietly stop reminding you of the one
    thing you most needed reminding of.
  * Deferrals recorded anywhere but the decision log and config.py.

__version__ : 1.0.0
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-29. First issue, at
#   Martin's request: "Ideally I would like to be reminded of deferred
#   decisions. These should be part of the daily report and work lists."

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG = ROOT / "working" / "DECISION_LOG.md"
REGISTER = ROOT / "working" / "updates" / "NRG_WORK_REGISTER.md"
TASKS = ROOT / "tools" / "task_register.csv"
CONFIG = ROOT / "src" / "utils" / "config.py"

GREEN, YELLOW, RED, DIM, RESET = (
    "\033[32m", "\033[33m", "\033[31m", "\033[2m", "\033[0m")

# Each marker is a form the corpus actually uses. Keep the list literal rather
# than clever: a regex broad enough to catch every phrasing also catches every
# discussion OF deferral, and a report that cries wolf is not read.
MARKERS = [
    r"not decided here",
    r"is Martin's call",
    r"Martin's call",
    r"pending Martin",
    r"deliberately not built",
    r"flagged, not built",
    r"awaiting sign-off",
    r"not yet written",
    r"not yet acted on",
    r"is owed",
    r"owed to Martin",
    r"needs a ruling",
    r"declined pending",
]
MARKER_RE = re.compile("|".join(MARKERS), re.I)
DISCHARGED_RE = re.compile(r"deferral discharged", re.I)
HEAD_RE = re.compile(r"^### (D-\d+)\s+(.*?)\s*\((\d{4}-\d{2}-\d{2}).*?status:\s*(\w+)",
                     re.I)


def decision_blocks(text: str):
    """(id, title, date, status, body) per decision entry."""
    lines = text.splitlines()
    starts = [i for i, l in enumerate(lines) if HEAD_RE.match(l)]
    for n, i in enumerate(starts):
        m = HEAD_RE.match(lines[i])
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        yield m.group(1), m.group(2), m.group(3), m.group(4), lines[i + 1:end]


def tracked_in(did: str) -> list[str]:
    """Which registers mention this decision id."""
    where = []
    for label, path in (("work register", REGISTER), ("task register", TASKS)):
        if path.exists() and did in path.read_text(encoding="utf-8"):
            where.append(label)
    return where


def main() -> int:
    if not LOG.exists():
        print(f"  {YELLOW}absent{RESET}   {LOG.relative_to(ROOT)}")
        return 0
    text = LOG.read_text(encoding="utf-8")

    hits = []
    for did, title, date, status, body in decision_blocks(text):
        if status.lower() != "active":
            continue
        if any(DISCHARGED_RE.search(l) for l in body):
            continue
        for line in body:
            m = MARKER_RE.search(line)
            if not m:
                continue
            ask = re.sub(r"[*`]", "", line).strip(" -").strip()
            hits.append((did, date, title, m.group(0), ask))
            break                                  # one line per decision

    cfg = []
    if CONFIG.exists():
        for n, line in enumerate(CONFIG.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"not yet acted on|pending Martin", line, re.I):
                cfg.append((n, re.sub(r"^#\s*", "", line).strip()))

    if not hits and not cfg:
        print(f"  {GREEN}OK{RESET}    no deferred decision is waiting")
        print("deferred_report: nothing outstanding")
        return 0

    print(f"  {YELLOW}{len(hits)} decision(s) deferred to a person "
          f"and still active:{RESET}")
    for did, date, title, marker, ask in hits:
        where = tracked_in(did)
        tag = (f"tracked in {' + '.join(where)}" if where
               else f"{RED}TRACKED NOWHERE{RESET}")
        print(f"      {did}  {date}  ({tag})")
        print(f"        {title[:96]}")
        print(f"        {DIM}→ {ask[:150]}{RESET}")
        print(f"        {DIM}  matched: \"{marker}\"{RESET}")

    if cfg:
        print(f"  {YELLOW}{len(cfg)} constant(s) carrying an un-acted-on "
              f"consequence:{RESET}")
        for n, line in cfg:
            print(f"      config.py:{n}  {line[:110]}")

    print(f"deferred_report: {len(hits) + len(cfg)} outstanding "
          f"(reported, not gated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
