#!/usr/bin/env python3
"""
repoint_index.py — refresh confirmed citation-index rows whose value has moved.

WHAT GOES WRONG WITHOUT IT

  `citation_index.csv` records, for each confirmed citation, the exact string a
  document quoted and sixty characters of context either side. When the pipeline
  is re-run and a coefficient changes, the document is rebuilt from the new
  outputs and the index is not. `cite_check` then says, correctly:

      REPOINT  CoeffShift_WMC3_b2_before: report9.md now quotes 1.996
               (index still says 2.017) — update the index row

  and there was no way to do that. `build_citation_index.py` proposes NEW rows
  and keys them on (key, document, quoted), so a row whose quoted string changed
  reads as a different row and the stale one is kept for ever.

WHAT IT WILL AND WILL NOT DO

  It moves a row onto the CURRENT rendering of the value the row is already
  about, in the document the row already names, and refreshes the stored
  context. It does not change which key a row is about, does not touch rejected
  rows, and does not create rows — that is still
  `build_citation_index.py`'s job.

  A row is left alone, and reported, when the current value cannot be found in
  that document at all. That means either the document dropped the citation or
  the value moved further than a re-render, and both deserve a person.

  IT DOES NOT ADJUDICATE. Before running this, satisfy yourself that the
  DOCUMENT agrees with the committed pipeline value and it is the index that is
  behind — the other way round is a stale document, and re-pointing the index
  would then bless the error. On 2026-08-23 the 22 rows were checked this way
  first: the committed CoeffShift values matched the documents to the last
  digit, and only the index was out of date.

Usage:
    python3 tools/repoint_index.py --dry-run
    python3 tools/repoint_index.py --apply
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-24.

import argparse
import csv
import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INDEX = REPO / "tools/citation_index.csv"
CTX = 60          # matches build_citation_index.CTX
# Characters of stored context that must still match. Twelve is short enough to
# survive a neighbouring number changing and long enough that two unrelated
# sentences do not reach it.
MIN_CONTEXT_MATCH = 12


def _load_cite_check():
    spec = importlib.util.spec_from_file_location(
        "cite_check", REPO / "tools/cite_check.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cite_check"] = mod
    spec.loader.exec_module(mod)
    return mod


def norm(s: str) -> str:
    return " ".join(s.split())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dp", nargs="+", type=int, default=[2, 3, 4])
    args = ap.parse_args()
    if not (args.apply or args.dry_run):
        ap.error("choose --dry-run or --apply")

    cc = _load_cite_check()
    docs = cc.load_documents()
    values = {}
    for _src, label, v in cc.collect_values():
        values.setdefault(label, v)

    with INDEX.open(encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        fields = rdr.fieldnames
        rows = list(rdr)

    moved, lost, same = [], [], 0
    for r in rows:
        if r.get("status") != "confirmed":
            continue
        v = values.get(r["key"])
        text = docs.get(r["document"])
        if v is None or text is None:
            lost.append((r, "key or document not found"))
            continue
        # PRECISION IS PART OF THE ROW. The stored string says how the document
        # renders this value — "1.762", three decimals — and a re-point must
        # stay at that precision. Taking the first dp that happens to be found
        # turns "+0.82" into "0.8244" and "1.762" into "1.74": not a correction
        # of a stale value but a move onto a different occurrence, in a
        # different rendering, possibly of a different sentence.
        want_dp = len(r["quoted"].split(".")[1]) if "." in r["quoted"] else 0
        order = [want_dp] + [d for d in args.dp if d != want_dp]

        # CONTEXT DECIDES WHICH OCCURRENCE. The row stores sixty characters
        # either side precisely so it can be re-found when a document renders
        # the same string more than once. Without it a re-point lands on
        # whichever occurrence comes first in the file.
        stored = cc._norm_ctx(r.get("before", "")), cc._norm_ctx(r.get("after", ""))
        hit = None
        for dp in order:
            s = cc.render(v, dp)
            if not cc.searchable(s, r["key"]):
                continue
            best, best_score = None, -1
            for a, b in cc.number_spans(text, s):
                bef = cc._norm_ctx(text[max(0, a - CTX):a])
                aft = cc._norm_ctx(text[b:b + CTX])
                score = (cc._common_tail(stored[0], bef)
                         + cc._common_head(stored[1], aft))
                if score > best_score:
                    best, best_score = (a, b), score
            if best is not None:
                hit = (s, best, best_score)
                break
        if hit is None:
            lost.append((r, "current value is not quoted in that document"))
            continue
        # THE DISCRIMINATOR. A row is stale only if the document has MOVED ON.
        # If the old rendering is still sitting at this row's own context, then
        # the document still quotes the old number and the pipeline has changed
        # underneath it — that is a stale DOCUMENT, and re-pointing the index
        # would quietly bless the error instead of reporting it. cite_check is
        # already shouting about those; this tool must not silence it.
        if r["quoted"] != cc.render(v, want_dp):
            for oa, ob in cc.number_spans(text, r["quoted"]):
                obef = cc._norm_ctx(text[max(0, oa - CTX):oa])
                oaft = cc._norm_ctx(text[ob:ob + CTX])
                if (cc._common_tail(stored[0], obef)
                        + cc._common_head(stored[1], oaft)) >= MIN_CONTEXT_MATCH:
                    lost.append((r, f"the document still quotes {r['quoted']} "
                                    f"here — stale document, not a stale index"))
                    break
            else:
                pass
            if lost and lost[-1][0] is r:
                continue

        s, (a, b), score = hit
        if score < MIN_CONTEXT_MATCH:
            lost.append((r, f"context match too weak ({score} chars) — "
                            f"the row may be about a different occurrence"))
            continue
        if s == r["quoted"]:
            same += 1
            continue
        moved.append((r, r["quoted"], s))
        r["quoted"] = s
        r["before"] = norm(text[max(0, a - CTX):a])
        r["after"] = norm(text[b:b + CTX])

    print(f"  {same} row(s) already current")
    print(f"  {len(moved)} row(s) re-pointed onto the current rendering\n")
    for r, was, now in moved:
        print(f"      {r['key']:<38} {was:>9} -> {now:<9} {r['document'].split('/')[-1]}")
    if lost:
        print(f"\n  {len(lost)} row(s) LEFT ALONE — a person is needed:")
        for r, why in lost:
            print(f"      {r['key']:<38} {why}")

    if not args.apply:
        print("\n  dry run — nothing written")
        return 0
    with INDEX.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"\n  written: {INDEX.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
