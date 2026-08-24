#!/usr/bin/env python3
"""
repoint_index.py — move confirmed citation-index rows onto the current value.

WHAT GOES WRONG WITHOUT IT

  `citation_index.csv` records, for each confirmed citation, the exact string a
  document quoted and sixty characters of context either side. Re-run the
  pipeline, rebuild the documents from the new outputs, and the index is left
  recording the old string. `cite_check` then says, correctly:

      REPOINT  CoeffShift_WMC3_b2_before: report9.md now quotes 1.996
               (index still says 2.017) — update the index row

  and there was no way to do it. `build_citation_index.py` proposes NEW rows and
  keys them on (key, document, quoted), so a row whose quoted string changed
  reads as a different row and the stale one survives for ever.

FINDING THE RIGHT OCCURRENCE — TWO WRONG ANSWERS FIRST

  1. "Take the first rendering that is found." That turned "+0.82" into "0.8244"
     and "1.762" into "1.74": not a correction of a stale value but a move onto
     a different occurrence, at a different precision, possibly in a different
     sentence. PRECISION IS PART OF THE ROW and is preserved.

  2. "Score candidates by how much of the stored context still matches." This
     refused 99 rows for "context match too weak" and was measuring the wrong
     thing. These values sit in TABLES, and the characters immediately before
     one are the rest of the same table row — other numbers, which changed in
     the same pipeline run. A contiguous-suffix comparison scores 0 to 4
     characters and never reaches the token that identifies the row.

  THE TOKEN THAT IDENTIFIES THE ROW IS ALREADY IN THE KEY.
  `CoeffShift_CEH20_b1_before` is well CEH20; `C2 (Dune) · beta_2` is cluster
  C2. `cite_check.anchor_groups()` extracts exactly those as SUBJECT anchors,
  and in a table the subject is the row label, on the same line as the value.
  So the test is a token test on the candidate's own line. Two rows of the same
  table cannot both satisfy it.

  Keys with no subject — prose citations like `Net_benefit` — fall back to the
  stored context, which is what it was always for and where it works.

WHAT IT REFUSES

  - More than one occurrence satisfying the test: ambiguous, not guessed.
  - The old rendering still sitting at the row's own context: that is a stale
    DOCUMENT, not a stale index, and re-pointing would bless the error instead
    of letting `cite_check` report it.
  - The current value not quoted in that document at all: the citation was
    dropped or moved further than a re-render, and a person should look.

  Rejected rows are never touched, and no row is created — that is still
  `build_citation_index.py`'s job.

  It does not adjudicate whether the DOCUMENT is right. Check that first: the
  document must agree with the committed pipeline value, and only the index be
  behind. On 2026-08-24 the flagged rows were checked that way — report9 quoted
  1.996 / 1.690 / 1.123 / 0.068 against committed 1.9959 / 1.6898 / 1.1228 /
  0.0683 — before any of this ran.

Usage:
    python3 tools/repoint_index.py --dry-run
    python3 tools/repoint_index.py --apply
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-24.

import argparse
import csv
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INDEX = REPO / "tools/citation_index.csv"
CTX = 60                 # matches build_citation_index.CTX
MIN_CONTEXT_MATCH = 12   # only used where the key names no subject
# How far from the value the subject may sit and still identify it. A table row
# label is a few dozen characters away; anything further is a passing mention.
SUBJECT_REACH = 80


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
    values: dict[str, float] = {}
    for _src, label, v in cc.collect_values():
        values.setdefault(label, v)

    with INDEX.open(encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        fields = rdr.fieldnames
        rows = list(rdr)

    moved, refused, same = [], [], 0

    for r in rows:
        if r.get("status") != "confirmed":
            continue
        v = values.get(r["key"])
        text = docs.get(r["document"])
        if v is None or text is None:
            refused.append((r, "key or document not found"))
            continue

        want_dp = len(r["quoted"].split(".")[1]) if "." in r["quoted"] else 0
        order = [want_dp] + [d for d in args.dp if d != want_dp]
        subj, _quant = cc.anchor_groups(r["key"])
        st_before = cc._norm_ctx(r.get("before", ""))
        st_after = cc._norm_ctx(r.get("after", ""))

        def near(a: int, b: int) -> str:
            """The value's immediate neighbourhood, clipped to its own line.

            NOT the whole line. In a markdown mirror a table row is a line and a
            prose paragraph is ALSO a line — often several hundred words. Testing
            the subject against a whole line therefore passes any paragraph that
            happens to mention C4 anywhere in it, and the first run duly
            re-pointed prose citations onto whichever number came first in such a
            paragraph. A row label sits within a few dozen characters of its
            value; a passing mention two hundred words away is not
            identification.
            """
            ls = max(text.rfind("\n", 0, a) + 1, a - SUBJECT_REACH)
            le = text.find("\n", b)
            le = min(le if le >= 0 else len(text), b + SUBJECT_REACH)
            return text[ls:le]

        def context_score(a: int, b: int) -> int:
            return (cc._common_tail(st_before, cc._norm_ctx(text[max(0, a - CTX):a]))
                    + cc._common_head(st_after, cc._norm_ctx(text[b:b + CTX])))

        hit = None
        problem = None
        for dp in order:
            s = cc.render(v, dp)
            if not cc.searchable(s, r["key"]):
                continue
            cands = list(cc.number_spans(text, s))
            if not cands:
                continue
            if subj:
                keep = [(a, b) for a, b in cands
                        if all(x.lower() in near(a, b).lower() for x in subj)]
                how = "subject"
            else:
                keep = [(a, b) for a, b in cands
                        if context_score(a, b) >= MIN_CONTEXT_MATCH]
                how = "context"
            if len(keep) == 1:
                hit = (s, keep[0], how)
                break
            if len(keep) > 1:
                problem = (f"{len(keep)} occurrences of {s} satisfy the {how} "
                           f"test — ambiguous, not guessing")
                break
        if problem:
            refused.append((r, problem))
            continue
        if hit is None:
            refused.append((r, "current value is not quoted in that document"))
            continue

        s, (a, b), how = hit

        # A row is stale only if the document has MOVED ON. If the old rendering
        # is still at this row's own place, the document still quotes the old
        # number while the pipeline has changed underneath it — a stale
        # DOCUMENT. Re-pointing then blesses the error instead of letting
        # cite_check report it.
        if s != r["quoted"]:
            for oa, ob in cc.number_spans(text, r["quoted"]):
                still_here = (all(x.lower() in near(oa, ob).lower() for x in subj)
                              if subj else context_score(oa, ob) >= MIN_CONTEXT_MATCH)
                if still_here:
                    problem = (f"the document still quotes {r['quoted']} here — "
                               f"stale document, not a stale index")
                    break
        if problem:
            refused.append((r, problem))
            continue

        if s == r["quoted"]:
            same += 1
            continue
        moved.append((r, r["quoted"], s, how))
        r["quoted"] = s
        r["before"] = norm(text[max(0, a - CTX):a])
        r["after"] = norm(text[b:b + CTX])

    print(f"  {same} row(s) already current")
    print(f"  {len(moved)} row(s) re-pointed\n")
    for r, was, now, how in moved:
        print(f"      {r['key']:<40} {was:>9} -> {now:<9} "
              f"{r['document'].split('/')[-1]:<34} by {how}")
    if refused:
        print(f"\n  {len(refused)} row(s) REFUSED:")
        for r, why in refused:
            print(f"      {r['key']:<40} {why}")

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
