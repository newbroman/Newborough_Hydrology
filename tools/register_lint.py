#!/usr/bin/env python3
"""Catch stale status cells in the work register before a human reads them.

WHY. On 2026-09-09 sixteen status cells in `working/updates/NRG_WORK_REGISTER.md`
were found to be wrong at once: eight finished tools written as "live, in
check_all" (which `nrg_status` does not classify as done, so the dashboard showed
a lane of 3 open as 11), three submission rows whose tasks had closed, three rows
waiting on pipeline runs that had already happened, a reopened row, and a header
asserting 133 decisions against a live 148. None of it was detectable, because a
status cell is prose and prose does not fail.

`tools/task_register.csv` already solved this for tasks: no row stores a status,
each carries a check command and the output it must produce, so a task closes
itself when the condition holds and reopens when it stops holding. This lint
brings the same discipline to the rows that cannot be moved there, by checking
the CLAIMS a status cell makes against the things that can answer them.

WHAT IT CHECKS. Only claims that are mechanically decidable — the lint is
deliberately narrow, because a gate that guesses gets switched off.

  1. TASK-LINKED. A cell naming a task (`T-01`, `T-24`) must not contradict
     `task_lint`. A cell that says done while its task is open, or that says
     open/awaiting while its task is done, is stale.

  2. GATE LIVENESS. A cell claiming a tool is "in check_all" must name a tool
     that `tools/check_all.sh` actually invokes.

  3. EXISTENCE. A cell asserting that a file does not exist yet ("no X yet",
     "X does not exist") is stale once X exists.

  4. BUNDLED IDS. A row whose ID cell names more than one work item hides
     those items behind a count of one. `W1, W2, W3, W4, W7, W8, W10` was one
     row for three weeks, so `nrg_status` printed "open 6" and then named
     twelve; four of the seven turned out to have no recoverable description at
     all, because nothing had ever been required to state one. A range
     (`W12-W15`) is the same defect. One row, one item.

  5. TYPED COUNTS (advisory). A cell stating "N entries/rows/wells/PDFs" has
     written down a number that its own command will contradict the next time it
     runs. Reported, never failed, because some are legitimately historical —
     but every one is a drift waiting to happen.

Usage:
    python3 tools/register_lint.py            # 1-4 gate, 5 advisory
    python3 tools/register_lint.py --counts   # also list every typed count
    python3 tools/register_lint.py --selftest # prove the checks can fail
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) — 2026-09-09. Check 4: a row
#   whose ID cell names more than one work item. Found by Martin, who noticed
#   the ledger showed more open items than the count claimed: one row read
#   `W1, W2, W3, W4, W7, W8, W10`, so the lane counted 6 open and named 12.
#   Four of those seven had no description left anywhere in either repository.
# v1.0.0  # Hollingham (2026) — 2026-09-09. First version.

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REGISTER = REPO / "working" / "updates" / "NRG_WORK_REGISTER.md"
CHECK_ALL = REPO / "tools" / "check_all.sh"

# The ID cell is taken WHOLE, not as a single well-formed id. The narrow
# pattern `[A-Z]+\d+[a-z]?` silently skipped every bundled row — which is
# precisely the row this lint most needs to see, and it would have made
# check 4 dead code. A cell that is not a single id is a finding, not a
# line to skip.
ROW = re.compile(r"^\|\s*\*\*(?P<id>[^|*]{1,80})\*\*\s*\|(?P<body>.*)\|\s*$")
# A single id, optionally with a word suffix naming a facet of the same item
# (`W98-history` is one row about one thing, not two rows in a trench coat).
ID_OK = re.compile(r"^[A-Z]+\d+[a-z]?(?:-[a-z]+)?$")

# Bundles that already exist. Pinned rather than demanded-fixed, the same shape
# as symbol_check's definition snapshot: the gate's job is to stop the register
# GAINING bundles, and a gate that first requires a backlog to be cleared is a
# gate that gets switched off. Each is printed on every run, so pinning is not
# hiding. Split one and delete its line.
BUNDLED_PINNED = {
    # Closed 2026-08-23, and every item in it verifiably so. Splitting a closed
    # bundle whose closures check out buys nothing but churn.
    "W12\u2013W15, W19, W21, W22, W25, W27",
}
TASK_REF = re.compile(r"\bT-(\d{2})\b")
DONE_ALT = r"done|closed|resolved|retired|superseded|withdrawn|complete\\w*"
OPEN_ALT = r"open|awaiting|not started|not done|outstanding|owed|todo|reopened|quick win|blocked"
DONE_WORD = re.compile(r"\b(done|closed|resolved|retired|superseded|withdrawn|complete)\b", re.I)
OPEN_WORD = re.compile(r"\b(open|awaiting|not started|not done|outstanding|owed|todo)\b", re.I)
NEGATED = re.compile(r"\b(?:not|never|no longer|un)\s+(?:done|started|closed|complete\w*)\b", re.I)
IN_CHECKALL = re.compile(r"in\s+`?check_all`?", re.I)
TOOLNAME = re.compile(r"`?\b([a-z_][a-z0-9_]{3,})\.py\b`?|`([a-z_][a-z0-9_]{3,})`")
NO_FILE_YET = re.compile(r"no\s+`?([\w./-]+\.(?:kml|csv|md|txt|json|py|odt|pdf))`?\s+(?:in\s+`?[\w./-]+`?\s+)?yet", re.I)
# An ID cell naming more than one item: a comma- or slash-separated list, or a
# range written with any of the dashes the register actually uses.
BUNDLED_ID = re.compile(r"[,/]|\s(?:and|&)\s|[0-9]\s*[-\u2010-\u2015]\s*[A-Za-z0-9]", re.I)
TYPED_COUNT = re.compile(r"\b(\d{1,5})\s+(entries|rows|wells|PDFs|files|occurrences|decisions|steps|documents)\b", re.I)


def task_states() -> dict[str, str]:
    """{'T-01': 'open'|'done'|'broken'} from task_lint, the tool that owns them."""
    try:
        out = subprocess.run([sys.executable, str(REPO / "tools" / "task_lint.py")],
                             capture_output=True, text=True, cwd=REPO, timeout=180).stdout
    except Exception:
        return {}
    states = {}
    for m in re.finditer(r"^\s*(DONE|OPEN|BROKEN)\s+(T-\d{2})\b", out, re.M):
        states[m.group(2)] = m.group(1).lower()
    return states


def check_all_invokes() -> str:
    return CHECK_ALL.read_text(encoding="utf-8") if CHECK_ALL.exists() else ""


def rows(text: str):
    for n, line in enumerate(text.split("\n"), 1):
        m = ROW.match(line)
        if not m:
            continue
        cells = [c.strip() for c in m.group("body").split("|")]
        yield n, m.group("id"), cells[-1] if cells else "", line


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        cases = [("**DONE 2026-09-09.** the KML exists", "done"),
                 ("open (not started)", "open"),
                 ("**CLOSED** - but not done in whole", "partial"),
                 ("live, in `check_all`", None),
                 ("**REOPENED 2026-09-09.** Original closure text: CLOSED 2026-09-05", "open"),
                 ("**Paper 2 DONE** - Paper 1 not started", "partial")]
        ok = all(_verdict(c) == w for c, w in cases)
        for c, w in cases:
            g = _verdict(c)
            if g != w:
                print(f"    want {w!r}, got {g!r}: {c[:60]!r}")
        print("  selftest:", "OK" if ok else "FAILED")
        return 0 if ok else 1

    text = REGISTER.read_text(encoding="utf-8")
    tasks = task_states()
    ca = check_all_invokes()
    bad = 0
    counts: list[str] = []

    for lineno, rid, status, _line in rows(text):
        if not status:
            continue
        verdict = _verdict(status)

        # 1. task-linked
        for tid in sorted({"T-" + m.group(1) for m in TASK_REF.finditer(status)}):
            state = tasks.get(tid)
            if not state or state == "broken":
                continue
            if verdict == "done" and state == "open":
                print(f"  STALE  {rid} (line {lineno}): the cell reads as settled but "
                      f"{tid} is OPEN in task_lint")
                bad += 1
            elif verdict == "open" and state == "done":
                print(f"  STALE  {rid} (line {lineno}): the cell reads as outstanding but "
                      f"{tid} is DONE in task_lint")
                bad += 1

        # 2. gate liveness
        if IN_CHECKALL.search(status) and ca:
            # Only .py names: a backticked word may be a function (check_claims)
            # or ordinary prose, and guessing produced this lint's first false
            # positive on T7.
            named = {m.group(1) for m in TOOLNAME.finditer(status) if m.group(1)}
            named -= {"check_all"}
            live = [t for t in named if t in ca]
            if named and not live:
                print(f"  STALE  {rid} (line {lineno}): claims a tool is in check_all, but "
                      f"none of {sorted(named)} is invoked in tools/check_all.sh")
                bad += 1

        # 3. existence
        for m in NO_FILE_YET.finditer(status):
            hits = list(REPO.glob(f"**/{Path(m.group(1)).name}"))
            hits = [h for h in hits if ".git" not in h.parts and "venv" not in h.parts]
            if hits:
                print(f"  STALE  {rid} (line {lineno}): says {m.group(1)!r} does not exist yet; "
                      f"it does — {hits[0].relative_to(REPO)}")
                bad += 1

        # 4. bundled IDs
        if not ID_OK.match(rid.strip()) and rid.strip() not in BUNDLED_PINNED:
            print(f"  BUNDLED  {rid!r} (line {lineno}): one row naming more than one "
                  f"work item — the lane counts it once and no gate can see the rest. "
                  f"Split it, one row per item.")
            bad += 1

        # 5. typed counts (advisory)
        for m in TYPED_COUNT.finditer(status):
            counts.append(f"    {rid} (line {lineno}): \"{m.group(0)}\"")

    if BUNDLED_PINNED:
        print(f"\n  {len(BUNDLED_PINNED)} pinned bundle(s) — rows naming more than one "
              f"work item, not yet split:")
        for b in sorted(BUNDLED_PINNED):
            print(f"    {b}")

    if counts:
        print(f"\n  {len(counts)} typed count(s) in status cells — advisory. Each is a number "
              f"a command can answer,\n  and will be wrong the next time that command runs.")
        if "--counts" in argv:
            for c in counts:
                print(c)
        else:
            print("  Run with --counts to list them.")

    print(f"\nregister_lint: {'OK' if bad == 0 else 'FAIL'}")
    return 1 if bad else 0


def _verdict(status: str) -> str | None:
    """done / open / partial / None.

    Order matters, and each rule earned its place on this lint's first run:

    - A cell whose HEAD reopens or defers ("REOPENED", "open", "awaiting")
      settles as open even when it quotes its own former closure further down.
      W26 does exactly that, and matching a done word anywhere called it settled.
    - A cell carrying both a done and an open marker is PARTIAL, never settled:
      S1's "Paper 2 DONE — Paper 1 not started" is one row covering two papers,
      and treating it as done hid an open task behind a closed-looking cell.
    - Only then does a head-anchored done word settle it.

    Returning None is a deliberate outcome: it means the cell states no verdict
    this lint is willing to act on, and no gate fires. Silence beats a guess.
    """
    head = NEGATED.sub(" ", status[:90])
    open_head = bool(re.match(r"\W*\**\s*(?:%s)\b" % OPEN_ALT, head, re.I))
    if open_head:
        return "open"
    done_anywhere = bool(DONE_WORD.search(NEGATED.sub(" ", status)))
    open_anywhere = bool(OPEN_WORD.search(status)) or bool(NEGATED.search(status))
    if done_anywhere and open_anywhere:
        return "partial"
    done_head = bool(re.match(r"\W*\**\s*(?:%s)\b" % DONE_ALT, head, re.I))
    if done_head or done_anywhere:
        return "done"
    if open_anywhere:
        return "open"
    return None


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
