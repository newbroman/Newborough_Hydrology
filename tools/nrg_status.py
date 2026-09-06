#!/usr/bin/env python3
"""
nrg_status.py — a status dashboard for working/updates/NRG_WORK_REGISTER.md.

Rebuilt 2026-09-05 from DECISION_LOG D-123. The original lived under gitignored
scratch/ ("committed nowhere", D-123) and was lost in the 2026-09-05 backups
clear-up; this is a faithful reconstruction from D-123's description, not the
original bytes. Promoted the same day from scratch/dashboard/ to tools/ (tracked,
alongside the other register-reading tools context_for / task_lint / deferred_report),
which retires the committed-nowhere risk D-123 flagged.

WHAT D-123 FIXED, AND THIS PRESERVES.

  The register's lanes do not share a column layout. Lane 2 ends in `Who`, not a
  status column; Lane 5 calls its status column `State`; Lane 3 has no status
  column at all. The original parser decided "is the last column a blocker?" with
  `"BLOCK" in cells[-1]` on the header row — which in Lane 2 tested `Who`, failed,
  and classified every row on its Who value, so W37/W39/W40 read open while their
  own text said CLOSED. The count published "68 open across all lanes" on that
  basis.

  So columns are located BY HEADER NAME, never by position: the status column is
  whichever header is `Status` or `State`; the blocker column is `BLOCKED-BY`.

  `unset` is NOT `open`. A row whose status the record does not state is counted
  as neither open nor done, and printed beside the open total — publishing the
  open count alone would let a lane of unadjudicated rows read as progress that
  did not happen (D-123).

  Ragged rows (a handful carry literal `|` inside cells and split into extra
  cells — W16, W51, W84, W90, W109) are handled, not crashed on: where a row's
  cell count does not match its header, the status is read from the LAST cell,
  which is where every lane that has one appends it.

USAGE
    python3 tools/nrg_status.py            # per-lane + total dashboard
    python3 tools/nrg_status.py --verbose  # also list open/blocked/partial IDs
    python3 tools/nrg_status.py --register PATH
"""
from __future__ import annotations

__version__ = "2.2.0"  # Hollingham (2026) — 2026-09-06. classify() is negation-aware.
#   A done marker was matched as a plain substring, so "not done" contained "done"
#   and read as done: Lane 5 reported S4 and S9 done when both cells say "not done",
#   and S1/S3 done when they are partial ("Paper 2 DONE … Paper 1 not started").
#   That published 5 of 11 JHRS requirements met against a true 1 done / 2 partial —
#   progress that had not happened, the same error D-123 exists to prevent.
# v2.1.0  # Hollingham (2026) — 2026-09-05. Promoted to tools/ (tracked).
# v2.0.0  # Hollingham (2026) — 2026-09-05. Rebuilt from D-123 after the scratch/
#   clear-up; header-name column lookup, unset counted apart from open.

import argparse
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_REGISTER = REPO / "working/updates/NRG_WORK_REGISTER.md"

STATUS_HEADERS = {"status", "state"}
BLOCKED_HEADERS = {"blocked-by", "blocked by"}
DONE_MARKERS = ("closed", "done", "resolved", "retired", "superseded", "withdrawn")
PARTIAL_MARKERS = ("partly", "partial")
EMPTY = {"", "-", "\u2014", "\u2013", "n/a", "na", "tbd", "unset"}

CLASSES = ("done", "open", "blocked", "partial", "unset")

# A done marker only counts where it is not negated. "not done" and "not started"
# are removed from the cell BEFORE the positive test, so the remaining text is
# what the row actually claims: nothing left means open, a surviving marker beside
# a negation means partly done.
NEGATED = re.compile(
    r"\bnot\s+(?:yet\s+)?"
    r"(?:done|started|built|applied|written|drafted|closed|complete\w*|resolved)\b"
    r"|\bnot\s+yet\b|\bnever\b"
    # A residual stated without "not": "Paper 1 highlights still unchecked".
    # Deliberately NOT the bare word "still", which is common in the prose that
    # narrates what a closure fixed and would demote closed rows to partial.
    r"|\bstill\s+(?:unchecked|outstanding|owed|open|pending|to\b|not\b)"
    r"|\bun(?:checked|written|applied|verified|started|resolved|reviewed)\b", re.I)
_EMPH = re.compile(r"[*`~_]+")
_DONE_ALT = "|".join(DONE_MARKERS)
HEAD_DONE = re.compile(r"^\W*(?:%s)\b" % _DONE_ALT, re.I)   # a verdict at the head settles it
ANY_DONE = re.compile(r"\b(?:%s)\b" % _DONE_ALT, re.I)

_SEP = re.compile(r"^\|[\s:\-|]+\|?\s*$")


def _cells(line: str) -> list[str]:
    """Split a markdown table row into stripped cell values."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _col_index(header: list[str], names: set[str]) -> int | None:
    for k, h in enumerate(header):
        if h.strip().lower() in names:
            return k
    return None


def parse_register(text: str) -> list[dict]:
    """Return the register's tables as lanes.

    Each lane is {name, header, s_idx, b_idx, rows}. A table is a `|`-row whose
    next line is a `|---|` separator; its lane name is the nearest heading above.
    """
    lines = text.splitlines()
    lanes: list[dict] = []
    heading = None
    i = 0
    while i < len(lines):
        ln = lines[i]
        st = ln.strip()
        if st.startswith("#"):
            heading = st.lstrip("#").strip()
        if st.startswith("|") and i + 1 < len(lines) and _SEP.match(lines[i + 1]):
            header = _cells(ln)
            rows = []
            j = i + 2
            # Collect data rows, continuing ACROSS blank lines and `---` rules
            # (Lane 2 carries a horizontal rule mid-table). Stop only at the next
            # heading or a new table header (a row whose next line is a separator).
            while j < len(lines):
                lj = lines[j]
                sj = lj.strip()
                if sj == "":
                    j += 1
                    continue
                if sj.startswith("#"):
                    break
                if re.fullmatch(r"-{3,}", sj):
                    j += 1
                    continue
                if sj.startswith("|"):
                    if _SEP.match(lj):
                        j += 1
                        continue
                    if j + 1 < len(lines) and _SEP.match(lines[j + 1]):
                        break            # a new table's header row
                    rows.append(_cells(lj))
                    j += 1
                    continue
                break                    # other prose ends the table
            lanes.append({
                "name": heading or "table",
                "header": header,
                "s_idx": _col_index(header, STATUS_HEADERS),
                "b_idx": _col_index(header, BLOCKED_HEADERS),
                "rows": rows,
            })
            i = j
            continue
        i += 1
    return lanes


def _status_value(row: list[str], header: list[str], s_idx: int | None) -> str:
    if s_idx is None:
        return ""
    if s_idx < len(row):
        # A ragged row (extra pipes) misaligns positional indices; the status is
        # always the appended LAST cell, so prefer that when the shape is off.
        if len(row) != len(header):
            return row[-1]
        return row[s_idx]
    return row[-1] if row else ""


def classify(row: list[str], header: list[str], s_idx: int | None,
             b_idx: int | None) -> str:
    item = row[1] if len(row) > 1 else ""
    status = _status_value(row, header, s_idx)
    blocked = row[b_idx] if (b_idx is not None and b_idx < len(row)) else ""
    cell = _EMPH.sub("", status).strip()
    st = cell.lower()
    negated = bool(NEGATED.search(cell))
    # Test the positive claim on the cell with its negated phrases removed, so
    # "not done" cannot satisfy it while "Paper 2 DONE … Paper 1 not started" can.
    positive = bool(ANY_DONE.search(NEGATED.sub(" ", cell)))
    # A verdict at the HEAD settles it: the prose after a closure routinely
    # narrates what was still wrong before, and must not reopen the row.
    if HEAD_DONE.match(cell):
        return "done"
    if item.strip().startswith("~~") and not negated:    # struck Item = closed (D-123)
        return "done"
    if positive and negated:                   # done in part, not in whole
        return "partial"
    if any(m in st for m in PARTIAL_MARKERS):
        return "partial"
    if positive:
        return "done"
    if "block" in st or blocked.strip().lower() not in EMPTY:
        return "blocked"
    # "unset" means a status column EXISTS and says nothing. A lane with no
    # status column (Lane 3) is judged on its Item and BLOCKED-BY above.
    if s_idx is not None and st in EMPTY:
        return "unset"
    return "open"


def _row_id(row: list[str]) -> str:
    raw = row[0] if row else ""
    return re.sub(r"[*`~]", "", raw).strip() or "?"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="NRG work-register status dashboard.")
    ap.add_argument("--register", default=str(DEFAULT_REGISTER))
    ap.add_argument("--verbose", "-v", action="store_true",
                    help="list the open / blocked / partial IDs per lane")
    a = ap.parse_args(argv[1:])

    reg = pathlib.Path(a.register)
    if not reg.exists():
        print(f"  ABORT  register not found: {reg}")
        return 2
    lanes = parse_register(reg.read_text(encoding="utf-8"))
    # Only lanes that actually track work: those with an ID-like first column.
    lanes = [L for L in lanes if L["header"] and L["header"][0].strip().lower() == "id"]

    grand = {c: 0 for c in CLASSES}
    print()
    print("=" * 70)
    print("NRG work-register status  —  unset is counted apart from open (D-123)")
    print("=" * 70)
    for L in lanes:
        tally = {c: 0 for c in CLASSES}
        listing = {"open": [], "blocked": [], "partial": []}
        for row in L["rows"]:
            c = classify(row, L["header"], L["s_idx"], L["b_idx"])
            tally[c] += 1
            grand[c] += 1
            if c in listing:
                listing[c].append(_row_id(row))
        n = sum(tally.values())
        scol = "by name" if L["s_idx"] is not None else "no status column"
        print(f"\n{L['name']}  ({n} rows, status: {scol})")
        print(f"    done {tally['done']:>3} | open {tally['open']:>3} | "
              f"unset {tally['unset']:>3} | blocked {tally['blocked']:>3} | "
              f"partial {tally['partial']:>3}")
        if a.verbose:
            for k in ("open", "blocked", "partial"):
                if listing[k]:
                    print(f"      {k:8}: {', '.join(listing[k])}")

    n = sum(grand.values())
    print("\n" + "-" * 70)
    print(f"TOTAL  ({n} rows)")
    print(f"    done {grand['done']:>3} | open {grand['open']:>3} | "
          f"unset {grand['unset']:>3} | blocked {grand['blocked']:>3} | "
          f"partial {grand['partial']:>3}")
    print(f"\n  {grand['open']} open, {grand['unset']} unset (record does not say) "
          "— unset is NOT progress.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
