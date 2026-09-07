#!/usr/bin/env python3
"""
doc_tier — which document family is LIVE to prose edits, and which are numbers-only.

Why this exists (D-144).

  Fifteen documents were live to prose edits at once, so every correction had to be
  carried into all of them and the changelog was mostly that carrying. Martin's
  ruling, 2026-09-07: finish the report, then everything refreshes from it. So at any
  time exactly one document family is live; every other document is numbers-only —
  tables regenerate (table_gen), numbers move (repoint_refs, doc_version_sync),
  symbols rename (symbol_apply) — but a SENTENCE changes only when the edit carries
  its reason: a D-number or a changelog delta id. `odt_edit._write` enforces it at
  the one place a byte reaches an ODT; this module is the lookup it uses.

The register is `tools/doc_tier.csv`. Its header comment row carries the current
phase; each row names a family (the ODT stem with its `_vN_N` suffix removed, the
same key session_handover derives), the phase in which it is live, its current
state, and the record that set it. Moving between phases is an edit to that file
citing a D-entry — `doc_tier_lint` checks the columns agree.

    from doc_tier import family, state, REASON_RE
    family("Newborough_Methods_Supplement_v1_9_114.odt")  -> "Newborough_Methods_Supplement"
    family("report10.odt")                                 -> "report"
    state("report")                                        -> "live" | "frozen" | None
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-07. First issue (D-144).

import csv
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTER = REPO / "tools" / "doc_tier.csv"
LOG = REPO / "working" / "doc_tier_log.csv"

STATES = ("live", "frozen")
# A reason is a decision number or a changelog delta id (date plus optional letter).
REASON_RE = re.compile(r"^(D-\d{3}|\d{4}-\d{2}-\d{2}[a-z]?)$")
# Mechanical callers: they move numbers, versions, symbols and references, never
# sentences. Each sets odt_edit.REASON to its own name once, at import.
EXEMPT_TOOLS = frozenset({"table_gen", "repoint_refs", "symbol_apply",
                          "fix_stale_refs", "doc_version_sync", "reembed_figures"})


def family(path) -> str | None:
    """Document family for an ODT/ODM path; None if the path is not one."""
    p = Path(path)
    if p.suffix.lower() not in (".odt", ".odm"):
        return None
    stem = re.sub(r"_v\d+(?:_\d+)*$", "", p.stem)
    if re.fullmatch(r"report\d*", stem):      # report6..report16 and report.odm
        return "report"
    return stem


def read_register() -> tuple[dict, dict[str, dict]]:
    """(header meta, {family: row}). Meta comes from the `# key=value` comment line."""
    meta, rows = {}, {}
    if not REGISTER.is_file():
        return meta, rows
    lines = REGISTER.read_text(encoding="utf-8").splitlines()
    body = []
    for line in lines:
        if line.startswith("#"):
            for m in re.finditer(r"(\w+)=(\S+)", line):
                meta[m.group(1)] = m.group(2)
        else:
            body.append(line)
    for row in csv.DictReader(body):
        if row.get("family"):
            rows[row["family"].strip()] = {k: (v or "").strip() for k, v in row.items()}
    return meta, rows


def state(fam: str) -> str | None:
    """'live', 'frozen', or None when the family has no row."""
    _meta, rows = read_register()
    row = rows.get(fam)
    return row["current"] if row else None


def reason_is_valid(reason: str | None) -> bool:
    return bool(reason) and (reason in EXEMPT_TOOLS or bool(REASON_RE.match(reason)))


def log_write(fam: str, dst, reason: str, n_subs: int, tag_change: bool) -> None:
    """Append one audit row for a write to a frozen document. Best-effort."""
    try:
        from datetime import datetime
        new = not LOG.is_file()
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["date", "family", "dst", "reason", "n_subs", "tag_change"])
            w.writerow([datetime.now().astimezone().isoformat(timespec="seconds"),
                        fam, Path(dst).name, reason, n_subs, int(bool(tag_change))])
    except OSError as exc:                     # a refused write must never block the edit
        print(f"  warn  doc_tier_log not written: {exc}")
