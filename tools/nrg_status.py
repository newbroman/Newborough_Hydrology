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

__version__ = "2.1.0"  # Hollingham (2026) — 2026-09-05. Promoted to tools/ (tracked).
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
    st = status.lower()
    if any(m in st for m in DONE_MARKERS):
        return "done"
    if item.strip().startswith("~~"):          # struck-through Item = closed (D-123)
        return "done"
    if any(m in st for m in PARTIAL_MARKERS):
        return "partial"
    if "block" in st or blocked.strip().lower() not in EMPTY:
        return "blocked"
    if status.strip().lower() in EMPTY:
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
