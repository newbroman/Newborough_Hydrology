#!/usr/bin/env python3
"""
build_citation_index.py
=======================
Propose an exact citation index: which document quotes which pipeline value,
as which literal string.

WHY NOT MARK UP THE DOCUMENTS
    The obvious "proper" fix is a marker beside every cited number, the way
    index.html carries <!--PL:key-->. The documents here are ODT edited in
    LibreOffice, so that would mean hand-placing hundreds of bookmarks and
    keeping them alive through every rewrite. This inverts it: the index lives
    beside the corpus, not inside it, and records the exact string each key is
    quoted as. Nothing in the ODTs changes, and the check becomes exact instead
    of proximity-guessed.

WHAT IT PRODUCES
    tools/citation_index.csv, one row per (key, document, quoted string):

        key, source_csv, document, quoted, before, after, status

    `before`/`after` are short normalised context slices used to relocate the
    citation when surrounding prose is edited. `status` is `confirmed` for rows
    a human has checked, `proposed` for rows this script suggested.

HOW IT DECIDES
    A row is proposed for every precision at which the CURRENT value of a key
    appears verbatim in a document, where an anchor token derived from the key
    sits nearby — the same
    anchoring cite_check uses, but applied to exact matches rather than near
    misses, so it proposes citations that are correct TODAY. Drift is then
    detected later, when the value moves and the indexed string no longer
    matches.

    Existing confirmed rows are never overwritten. Re-running only adds.

Usage:
    python3 tools/build_citation_index.py            # propose, write index
    python3 tools/build_citation_index.py --dry-run  # print, write nothing
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INDEX = REPO / "tools" / "citation_index.csv"
CTX = 60          # characters of context stored either side
FIELDS = ["key", "source_csv", "document", "quoted", "before", "after",
          "confidence", "status"]

# Anchor distance decides confidence. A key token sitting within TIGHT
# characters of the number is strong evidence the number IS that quantity; one
# 400 characters away is barely evidence at all in a per-well table. Only tight
# proposals are written by default: a starting index that is mostly right and
# small enough to review beats a complete one nobody checks.
TIGHT = 90


def _load_cite_check():
    """Reuse cite_check's corpus loading, value collection and anchoring, so the
    two tools can never disagree about what counts as a citation."""
    spec = importlib.util.spec_from_file_location(
        "cite_check", REPO / "tools" / "cite_check.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def norm(s: str) -> str:
    return " ".join(s.split())


def existing_rows() -> list[dict]:
    if not INDEX.exists():
        return []
    with open(INDEX, encoding="utf8") as fh:
        return list(csv.DictReader(fh))


class _Span:
    """Minimal stand-in for a regex match: number_spans yields plain offsets,
    and the proposal loop below reads .start() and .end()."""

    __slots__ = ("_s", "_e")

    def __init__(self, s: int, e: int):
        self._s, self._e = s, e

    def start(self) -> int:
        return self._s

    def end(self) -> int:
        return self._e


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dp", nargs="+", type=int, default=[2, 3, 4])
    ap.add_argument("--all", action="store_true",
                    help="also propose loose (low-confidence) matches")
    args = ap.parse_args()

    cc = _load_cite_check()
    docs = cc.load_documents()
    if not docs:
        print("No mirrors found — run tools/refresh_mirrors.py first.")
        return 1

    old = existing_rows()
    have = {(r["key"], r["document"], r["quoted"]) for r in old}
    kept_confirmed = sum(1 for r in old if r.get("status") == "confirmed")

    proposed: list[dict] = []
    seen_values: set[tuple[str, float]] = set()

    for source, label, v in cc.collect_values():
        if not abs(v) > 0:
            continue
        if (label, v) in seen_values:      # consolidated files republish values
            continue
        seen_values.add((label, v))
        anc = cc.anchors(label)

        for dp in args.dp:
            s = cc.render(v, dp)
            if not cc.searchable(s):
                continue
            hit = False
            for dname, text in docs.items():
                # A history document records what a value USED to be, so a
                # citation row pointing at one would go red exactly when it was
                # doing its job. cite_check skips these in the citation check;
                # proposing them here would put them straight back.
                if dname.split("/")[-1] in cc.HISTORY_DOCS:
                    continue
                # cc.number_spans, NOT re.finditer(re.escape(s)). The two are
                # not equivalent and the difference was a systematic blind
                # spot: render() emits an ASCII hyphen, the mirrors carry the
                # typographic minus U+2212, and a literal search therefore
                # matched NO negative value anywhere in the corpus. On
                # 2026-09-03 the index held 337 rows of which 13 were negative,
                # and 11 of those had been written by hand that day. Script
                # 38's transect trend — quoted as "−28.2" in report9 and Paper
                # 1, 151 characters from its own anchor — proposed nothing at
                # any precision.
                #
                # cite_check's own checker has always been minus-tolerant, so
                # the builder and the check were using different matchers.
                # Sharing one means the builder proposes exactly what the check
                # can find, and inherits its whole-number and citable-context
                # guards for free.
                for _s0, _e0 in cc.number_spans(text, s):
                    m = _Span(_s0, _e0)
                    lo = text[max(0, m.start() - cc.ANCHOR_WINDOW):
                              m.start() + cc.ANCHOR_WINDOW].lower()
                    tight = text[max(0, m.start() - TIGHT):
                                 m.start() + TIGHT].lower()
                    if anc:
                        if any(a.lower() in tight for a in anc):
                            conf = "high"
                        elif any(a.lower() in lo for a in anc):
                            conf = "low"
                        else:
                            continue
                    else:
                        conf = "low"          # nothing to anchor on
                    if conf == "low" and not args.all:
                        continue
                    key = (label, dname, s)
                    if key in have:
                        hit = True
                        continue
                    proposed.append({
                        "key": label,
                        "source_csv": source,
                        "document": dname,
                        "quoted": s,
                        "before": norm(text[max(0, m.start() - CTX):m.start()]),
                        "after": norm(text[m.end():m.end() + CTX]),
                        "confidence": conf,
                        "status": "proposed",
                    })
                    have.add(key)
                    hit = True
            # NO break. A value quoted at 2 dp in prose and 3 dp in a table is
            # two separate citations in two separate places, and the table one
            # is usually the more important. Stopping at the first precision
            # that matched left the full-precision table renderings — the ones
            # that ARE the CSV — entirely unindexed.
            _ = hit

    rows = old + proposed
    print(f"existing rows: {len(old)} ({kept_confirmed} confirmed)")
    print(f"newly proposed: {len(proposed)}")
    by_doc: dict[str, int] = {}
    for r in proposed:
        by_doc[r["document"]] = by_doc.get(r["document"], 0) + 1
    for d, n in sorted(by_doc.items(), key=lambda kv: -kv[1]):
        print(f"  {n:4d}  {d}")

    if args.dry_run:
        print("\n(dry run — nothing written)")
        return 0

    INDEX.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX, "w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {INDEX.relative_to(REPO)} ({len(rows)} rows)")
    print("Review the `proposed` rows and set status=confirmed on the ones that "
          "are genuine citations.")
    print("Until a row is confirmed it is still checked, but a failure on a "
          "proposed row means 'check this', not 'this is broken'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
