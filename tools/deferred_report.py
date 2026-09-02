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

__version__ : 1.2.0
"""
from __future__ import annotations

__version__ = "1.2.0"  # Hollingham (2026) — 2026-09-02. Two precision
#   faults, both found by this tool flagging D-116 the hour it was written.
#
#   THE LABEL RULE WAS DEFEATED BY A PARENTHETICAL. v1.1.0 exempts a marker
#   under a recording label, matching the captured text against
#   DECIDED_LABELS verbatim. D-116 was drafted as "**Decision (Martin's
#   ruling, this date):**", which captures as "decision (martin's ruling, this
#   date)" and is in no set; the exemption silently lapsed and an entry
#   RECORDING a ruling was reported as deferring one. Labels are now
#   normalised — a trailing parenthetical is stripped before the lookup.
#
#   BE CLEAR ABOUT WHAT THIS FIX IS WORTH. I first wrote that the log "uses
#   that form freely". IT DOES NOT: 115 of 116 entries write a bare
#   "**Decision:**" and the only exception was mine, written an hour earlier.
#   D-116 has since been conformed, so on the log as it stands this guard is
#   PROPHYLACTIC, not load-bearing — and it is kept because the same
#   brittleness is demonstrably not confined to this tool:
#   build_public_decisions.py keys on the same exact string and DROPPED D-116
#   FROM THE PUBLIC EXPORT for the same reason, in the same hour. It at least
#   said so ("no Decision statement — refusing to guess"); this tool failed
#   silently, in the direction of a false alarm. A rule keyed on an exact
#   string is defeated by any prose that decorates the string.
#
#   AND A NEGATED OBLIGATION READ AS AN OBLIGATION. D-116 states "no document
#   edit is owed" — the ABSENCE of work — and "is owed" matched it. Markers
#   that name an obligation are now checked against the text preceding them on
#   the line, and a negator there (no / none / nothing / neither / nor) means
#   the sentence is denying the obligation, not recording one. Applied only to
#   NEGATABLE_MARKERS: markers whose own wording is already negative
#   ("not yet written") would be inverted by their own text.
#   The check spans the PRECEDING LINE too. Written line-locally it was inert
#   on the very case it was written for — the log wraps at ~78 characters and
#   D-116's "no" ends one line while "is owed" opens the next. The aggregate
#   count hid that, because the label fix suppressed the same entry on its own;
#   toggling each fix separately is what showed the guard doing nothing.
#
#   Neither fix moves any other flag: measured by toggling each independently,
#   v1.1.0 reports {D-050, D-116} and label-only, negation-only and both each
#   report {D-050}. With D-116 conformed BOTH guards are now prophylactic on
#   this log, which is exactly why --selftest exists: a guard whose only
#   evidence is that the corpus currently contains nothing for it to catch is
#   a guard nobody can tell has stopped working. The self-test carries its own
#   cases and does not depend on what the log happens to hold.
#
# v1.1.0  # Hollingham (2026) — 2026-09-02. A marker only counts
#   where it is DOING the deferring: not under a label that records a decision
#   (Question / Decision / Rationale / Retires / Traces to / Revisit-if / Also
#   recorded), and not on a line carrying the local opt-out <!-- decided -->.
#   Measured on the log the day it was written: three of eight standing flags
#   were markers inside decisions already made, and D-099's match was the
#   sentence stating the decision taken. Genuine deferrals sit under Requires,
#   Not adopted, or Not decided here, and none of them moves.
#
#   TWO FURTHER MODES ARE NOT FIXED HERE and are recorded so they are not
#   rediscovered. Quoting a marker while RECORDING a ruling re-triggers it —
#   writing D-113 and D-114 took the count 10 to 12 before it fell — which the
#   label rule mostly handles, since a quotation usually lands under Question or
#   Rationale. And decision_blocks() ends a block at the next `### D-`, so prose
#   appended after the LAST entry is attributed to it: D-114 was briefly
#   reported carrying D-100's text. Free-standing notes belong inside the entry
#   they concern, which is also what the discharge marker requires.
#
# v1.0.0  # Hollingham (2026) — 2026-08-29. First issue, at
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

# Markers that NAME AN OBLIGATION can be negated by the sentence carrying them;
# markers whose own wording is already negative ("not yet written") cannot,
# because their own "not" would trip the guard. Only the first kind is checked.
NEGATABLE_MARKERS = ("is owed", "owed to Martin", "needs a ruling")
NEGATOR_RE = re.compile(r"\b(no|none|nothing|neither|nor)\b", re.I)


def _negated(prev: str, line: str, m: re.Match) -> bool:
    """True when the marker is being DENIED rather than raised.

    D-116 records that *no* document edit is owed — the absence of work — and
    v1.1.0 reported it as a deferral. The negator has to be in the same clause,
    so the search is bounded at the nearest preceding clause break rather than
    running to the start of the text: an earlier sentence saying "no" about
    something else must not exempt a real obligation later on.

    THE PRECEDING LINE IS PART OF THE CLAUSE. The log hard-wraps at about 78
    characters, so a negator and the marker it governs land on different lines
    as often as not — D-116's "no" ends line 7047 and "is owed" opens 7048.
    Written line-locally this guard was INERT on the exact case it was written
    for, which the aggregate count did not show because the label fix was
    independently suppressing the same entry. Testing each fix in isolation is
    what exposed it.
    """
    if not any(k.lower() in m.group(0).lower() for k in NEGATABLE_MARKERS):
        return False
    before = prev + " " + line[:m.start()]
    clause = re.split(r"[.;:]|\u2014|--", before)[-1]
    return bool(NEGATOR_RE.search(clause))
DISCHARGED_RE = re.compile(r"deferral discharged", re.I)

# ── Where a marker has to be to count (T16b) ─────────────────────────────────
#
# A marker APPEARING is not a deferral; a marker DOING THE DEFERRING is. Until
# 2026-09-02 this tool matched the phrase anywhere in an entry, and three of the
# eight flags then standing were its own noise — every one of them a marker
# sitting inside a decision that had been fully made:
#
#   D-032  "Martin's call" inside a clause the entry itself marks withdrawn
#   D-081  "is owed" in "the attribution it carries IS OWED BY coast1900.kml",
#          a requirement on a file rather than something owed to a person
#   D-099  "is Martin's call" in the sentence STATING THE DECISION TAKEN —
#          "altering a published figure is Martin's call, not a side effect of
#          adding a measurement, so the break gets 12_02_break_in_slope.png"
#
# Measured across the log: genuine deferrals sit under Requires, Not adopted,
# Not decided here, or a prose sub-heading that is itself an open item. The
# false ones sit under Decision. So a marker under a label that RECORDS rather
# than DEFERS does not count.
DECIDED_LABELS = {
    "question", "decision", "rationale", "also recorded", "retires",
    "traces to", "revisit-if", "deferral discharged",
}
LABEL_RE = re.compile(r"^\s*-\s+\*\*([^:*]+?):?\*\*")

# A label may carry a parenthetical qualifier — "**Decision (Martin's ruling,
# this date):**" — and the set lookup is exact, so the qualifier put the label
# outside every recognised name and the exemption silently lapsed. Strip it.
_LABEL_QUALIFIER_RE = re.compile(r"\s*\([^)]*\)\s*$")


def _label_key(raw: str) -> str:
    return _LABEL_QUALIFIER_RE.sub("", raw).strip().lower()

# The local opt-out, same idiom as docref_lint's `<!-- former path -->`: a line
# that names a decision as someone's to make, while recording that it was made,
# marks itself. Local to the line, so there is no central exemption list to
# maintain and no way for an exemption to outlive the text it exempts.
DECIDED_INLINE = "<!-- decided -->"
HEAD_RE = re.compile(r"^### (D-\d+)\s+(.*?)\s*\((\d{4}-\d{2}-\d{2}).*?status:\s*(\w+)",
                     re.I)


def deferring_line(body):
    """The first line of `body` that is DOING a deferral, or None.

    The single implementation of the marker/label/negation rules. It exists as
    a function because this file's own v1.1.0 note records what happens
    otherwise: edit() carried its own copy of odt_edit's guard block and a fix
    landed in the copy nothing called. --selftest and main() run THIS, so a
    guard that stops working stops working in both places at once.
    """
    label, prev = None, ""
    for line in body:
        lm = LABEL_RE.match(line)
        if lm:
            label = _label_key(lm.group(1))
        m = MARKER_RE.search(line)
        if not m:
            prev = line
            continue
        if DECIDED_INLINE in line:
            continue                               # the line marks itself
        if _negated(prev, line, m):
            continue                               # denying it, not raising it
        if label in DECIDED_LABELS:
            continue                               # recording, not deferring
        return line, m
    return None


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
        found = deferring_line(body)
        if found:
            line, m = found
            ask = re.sub(r"[*`]", "", line).strip(" -").strip()
            hits.append((did, date, title, m.group(0), ask))

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


# ── Self-test ────────────────────────────────────────────────────────────────
#
# Both v1.2.0 guards are prophylactic on the log as it stands: the one entry
# that exercised them was conformed the same hour. A guard whose only evidence
# is "the corpus contains nothing for it to catch" is a guard nobody can tell
# has stopped working, so the cases live here instead of relying on the log.
#
# Run: python3 tools/deferred_report.py --selftest
_SELFTEST = [
    # (name, entry body, should this entry be reported?)
    ("bare Decision label exempts",
     ["- **Decision:** the attribution is owed to Martin."], False),
    ("parenthetical Decision label ALSO exempts (v1.2.0)",
     ["- **Decision (Martin's ruling, 2026-09-02):** the attribution is owed",
      "  to Martin."], False),
    ("negated obligation on one line is not a deferral (v1.2.0)",
     ["- **Requires:** nothing is owed here."], False),
    ("negated obligation ACROSS A WRAP is not a deferral (v1.2.0)",
     ["- **Requires:** the passages stand as written; **no",
      "  document edit is owed.**"], False),
    ("a real obligation under Requires IS a deferral",
     ["- **Requires:** a ruling on the header is owed to Martin."], True),
    ("a negator about something else does not exempt",
     ["- **Requires:** no figure moves. A ruling is owed to Martin."], True),
    ("an already-negative marker is not inverted by its own text",
     ["- **Requires:** the century paragraph is not yet written."], True),
    ("Rationale is a recording label",
     ["- **Rationale:** altering a published figure is Martin's call."], False),
]


def _selftest() -> int:
    bad = 0
    for name, body, want in _SELFTEST:
        got = deferring_line(body) is not None
        ok = got == want
        bad += not ok
        mark = f"{GREEN}ok{RESET}" if ok else f"{RED}FAIL{RESET}"
        print(f"  {mark}  {name}  (reported={got}, expected={want})")
    print(f"deferred_report --selftest: {len(_SELFTEST) - bad}/{len(_SELFTEST)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv else main())
