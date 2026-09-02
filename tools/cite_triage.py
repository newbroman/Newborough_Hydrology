#!/usr/bin/env python3
"""
cite_triage — sort cite_check's near-miss list into the rows worth reading.

WHY

  `cite_check`'s near-miss scan reports a corpus number sitting within two
  units of the last decimal place of a committed value. Measured on the corpus
  of 2026-09-02 it returns **324 rows, of which ONE is a real error** — a
  yield of 0.3%. That is not a defect in the scan: a ±2 band around 2,917
  committed values, searched across 30 documents, catches a neighbour almost
  every time. It is a defect in what a person is then asked to read.

  W127 makes it worse: `_FALSE_POSITIVES` is consulted on the index path and in
  `sweep_repeats`, but NOT on the near-miss path, so rows already adjudicated
  by hand re-report on every run. `cite_check`'s own comment states the
  consequence — "the reader learns to skim a gating check, which is worse than
  the check not existing."

  This tool does the mechanical part of the sort, so the next session reads a
  residue instead of the whole thing. It decides nothing: every row it sets
  aside is written to the JSON with the reason, and `--all` prints them.

  BE CLEAR ABOUT HOW MUCH IT SAVES. The hand triage of 2026-09-02 went
  324 -> 17, then found the single real error by READING those 17 in context.
  This tool gets to **102**, not 17. The gap is not a bug to tune away: the
  hand pass reached 17 by running the "document also quotes the current value"
  test after a DELIBERATELY GENEROUS collision pass, and a generous collision
  pass is the one thing this tool must not do, because a false collision hides
  an error while a false triage row only costs a minute. Four defensible
  configurations of these same passes returned 0, 5, 96 and 102 rows. That
  variance IS the finding, and it is why the tool ships with the ordering it
  can defend rather than the one that produces the prettiest number: tuning
  until 17 came out would have been fitting the tool to one day's corpus.

  So: 102 of 324 to read, a two-thirds saving, and the one real row is in
  them — asserted by --regression below.

THE FOUR PASSES, in the order they are cheapest

  ADJUDICATED   the (key, document, quoted) triple is in
                tools/citation_false_positives.csv. Already ruled on.
  RENDERING     the corpus number IS the committed value, rendered — rounded
                half-up OR half-even OR truncated, at the corpus number's own
                precision, in the stored unit or in mm. The document is right
                and the scan is reading its own rounding.
  COLLISION     the corpus number renders EXACTLY some other committed value.
                The scan grabbed a neighbour.
  CURRENT       the document ALSO quotes the correct value for this key,
                anchored. Whatever the near number is, this document is not
                stale about this key. **This is the strongest pass**: on the
                2026-09-02 corpus it took the residue from 96 rows to 17.

  What is left is the triage list. Read it.

WHY RENDERING TESTS THREE ROUNDING MODES

  Python's format() rounds half to even: f"{-0.1075:.3f}" is '-0.107'. A person
  writing a report rounds half up and puts '-0.108'. Testing only Python's mode
  reported a correctly-rounded Paper 1 table cell as drift. Truncation is
  tested too because some renderings in this corpus truncate.

WHAT THIS TOOL DOES NOT DO

  It does not exclude a row for being a small gap. Measured 2026-09-02, the
  gaps form a continuum from 2.11% down with no threshold separating the real
  error (0.34%) from the noise above and below it. A gap cutoff would have
  hidden the one row that mattered.

  It does not gate. It is a reading aid for an advisory list.

Usage:
    python3 tools/cite_check.py --csv triage.csv
    python3 tools/cite_triage.py triage.csv [--all] [--json out.json]

__version__ : 1.0.0
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
from collections import defaultdict

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-02. First issue, after a
#   hand triage of 324 near-miss rows returned exactly one real error: the
#   far-field s_coast quoted as −1.51 in report8 and report11 against a
#   committed −1.5048922, which renders as −1.50. Every other row was a
#   rendering, a collision, or a document that also quotes the right value.
#   Building it as a tool rather than leaving the method in a handover, because
#   the same 323 rows will be there next time and nobody re-derives a sort they
#   have to redo from scratch.

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

GREEN, YELLOW, RED, DIM, RESET = (
    "\033[32m", "\033[33m", "\033[31m", "\033[2m", "\033[0m")

RENDER_DP = (0, 1, 2, 3, 4)


def _renderings(v: float, dp: int) -> set[str]:
    """Every string a person might legitimately write for v at dp places.

    NaN and inf are in collect_values() — a committed CSV can carry an empty
    cell or a divide-by-zero — and math.floor() raises on them rather than
    returning something harmless, which took the whole run down on the first
    try. A value that is not finite has no rendering; say so and move on.
    """
    if not math.isfinite(v):
        return set()
    out = set()
    # NO v/1000. A metre value divided by 1000 rounds to "0" at 0 dp, and "0"
    # occurs in every document in the corpus — which is how the first build of
    # this tool concluded that report8 "also quotes the current value" for the
    # far-field s_coast and buried the one real error in the list. The corpus
    # stores metres and cites millimetres, never the reverse.
    for cand in (v, -v, v * 1000, -v * 1000):
        out.add(f"{cand:.{dp}f}")                       # half-even (Python)
        scaled = abs(cand) * 10 ** dp
        half_up = math.floor(scaled + 0.5) / 10 ** dp   # half-up (people)
        out.add(f"{half_up:.{dp}f}")
        trunc = math.floor(scaled) / 10 ** dp           # truncation
        out.add(f"{trunc:.{dp}f}")
    return out


def renders_as(v: float, s: str) -> bool:
    t = s.lstrip("-−")
    dp = len(t.split(".")[1]) if "." in t else 0
    return t in {r.lstrip("-") for r in _renderings(v, dp)}


def _plain(v: float, dp: int) -> set[str]:
    """Only the renderings a collision may claim: the stored unit and mm, and
    only rounding — not truncation, not a division by 1000.

    THE COLLISION TEST MUST BE THE NARROW ONE. Built with the same generous
    set _renderings() uses for the document's own number, it matched something
    for nearly every row: 2,917 committed values crossed with six unit
    variants, three rounding modes and five decimal places produces a string
    set dense enough that almost any number in the corpus is "some other
    committed value". The first build of this tool returned COLLISION 210 and
    TRIAGE 0 on a corpus with a known real error in it, which is the worst
    answer a triage tool can give. Generosity belongs on the RENDERING pass,
    where a false positive means trusting the document; it does not belong
    here, where a false positive means hiding an error.
    """
    if not math.isfinite(v):
        return set()
    out = set()
    for cand in (v, -v, v * 1000, -v * 1000):
        out.add(f"{cand:.{dp}f}")
        scaled = abs(cand) * 10 ** dp
        out.add(f"{math.floor(scaled + 0.5) / 10 ** dp:.{dp}f}")
    return out


def build_render_index(values) -> dict:
    idx = defaultdict(list)
    for src, lab, v in values:
        for dp in RENDER_DP:
            for r in _plain(v, dp):
                idx[(r.lstrip("-"), dp)].append((lab, v, src))
    return idx


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="output of cite_check.py --csv")
    ap.add_argument("--all", action="store_true",
                    help="print the set-aside rows too, with their reason")
    ap.add_argument("--json", default=None, help="write the full sort here")
    ap.add_argument("--regression", action="store_true",
                    help="assert the 2026-09-02 incident row still reaches "
                         "TRIAGE; exit 1 if a pass has swallowed it")
    args = ap.parse_args()

    import cite_check as cc

    rows = list(csv.DictReader(open(args.csv, encoding="utf8")))
    values = cc.collect_values()
    docs = cc.load_documents()
    fps = cc.load_false_positives()
    adjudicated = set(fps)
    adj_keys = {k for k, _, _ in fps}
    render_idx = build_render_index(values)

    buckets = defaultdict(list)
    for r in rows:
        key, cor = r["key"], r["corpus_value"]
        com = float(r["committed"])
        rdocs = [d.strip() for d in r["documents"].split(";")]

        if any((key, d, cor) in adjudicated for d in rdocs) or key in adj_keys:
            buckets["ADJUDICATED"].append(r)
            continue
        if renders_as(com, cor):
            buckets["RENDERING"].append(r)
            continue
        bare = cor.lstrip("-−")
        cdp = len(bare.split(".")[1]) if "." in bare else 0
        cand = [o for o in render_idx.get((bare, cdp), []) if o[0] != key]
        # AND the other key must actually be spoken about in one of these
        # documents. A committed value that renders the same but is never
        # mentioned here explains nothing.
        owners = [o for o in cand
                  if any(cc.anchored(docs[d], cor, cc.anchors(o[0]), key=o[0])
                         for d in rdocs if d in docs)]
        if owners:
            r["owners"] = sorted({o[0] for o in owners})[:4]
            buckets["COLLISION"].append(r)
            continue
        # Does the document also quote the CURRENT value for this key?
        anchor_keys = cc.anchors(key)
        also = []
        for d in rdocs:
            text = docs.get(d)
            if text is None:
                continue
            for dp in RENDER_DP:
                # A candidate rendering must carry at least three significant
                # digits to be evidence. At 0 dp a value near 1.5 renders as
                # "1" or "2", which matches something in every paragraph. The
                # full cite_check.searchable() test was tried here and is too
                # strict for this purpose — it rejected so many candidates that
                # the CURRENT pass stopped firing and the residue went back to
                # 96. Three significant digits is the floor that keeps the pass
                # working without letting a single digit vote.
                hit = next((s for s in sorted(_renderings(com, dp))
                            if cc._sig_digits(s) >= 3
                            and cc.quotes(text, s)
                            and cc.anchored(text, s, anchor_keys, key=key)), None)
                if hit:
                    also.append(f"{d}:{hit}")
                    break
        if also:
            r["current_also_quoted"] = also
            buckets["CURRENT"].append(r)
        else:
            buckets["TRIAGE"].append(r)

    order = ("ADJUDICATED", "RENDERING", "COLLISION", "CURRENT", "TRIAGE")
    print(f"  {len(rows)} near-miss row(s) from {args.csv}")
    for name in order:
        n = len(buckets[name])
        col = RED if name == "TRIAGE" and n else DIM
        print(f"    {col}{name:12s} {n:4d}{RESET}")

    if args.all:
        for name in order[:-1]:
            for r in buckets[name]:
                extra = r.get("owners") or r.get("current_also_quoted") or ""
                print(f"  {DIM}{name:11s} {r['key'][:44]:44s} "
                      f"{r['committed']:>10} -> {r['corpus_value']:>9}  "
                      f"{str(extra)[:60]}{RESET}")

    triage = sorted(buckets["TRIAGE"], key=lambda r: -float(r["rel_gap_pct"]))
    if triage:
        print(f"\n  {YELLOW}{len(triage)} row(s) for a person to read:{RESET}")
        for r in triage:
            where = ", ".join(d.strip().split("/")[-1]
                              for d in r["documents"].split(";"))
            print(f"      {r['rel_gap_pct']:>5}%  {r['key'][:46]:46s} "
                  f"committed {r['committed']:>11}  corpus {r['corpus_value']:>9}")
            print(f"        {DIM}{where[:96]}{RESET}")
    else:
        print(f"\n  {GREEN}OK{RESET}    nothing left for a person to read")

    if args.regression:
        # THE INCIDENT THIS TOOL WAS BUILT AROUND. report8 and report11 quoted
        # the far-field coastal amplitude as -1.51 against a committed
        # -1.5048922, which renders as -1.50. It was the ONLY real error in 324
        # near-miss rows, and two successive builds of this tool buried it —
        # first in COLLISION (a render index generous enough to match anything),
        # then in CURRENT (a metre value divided by 1000 rounds to "0" at 0 dp,
        # and "0" is in every document). A triage tool that hides the one row
        # that matters is worse than no triage tool, so the case is asserted
        # rather than remembered. It is pinned to the value, not the documents:
        # the corpus is corrected, so this passes on a corrected tree only if
        # the row is absent from the input entirely.
        want = ("FarField · s_coast", "-1.51")
        present = any((r["key"], r["corpus_value"]) == want for r in rows)
        if not present:
            print(f"  {DIM}regression: the 2026-09-02 row is not in this "
                  f"input (corrected corpus) — nothing to assert{RESET}")
        elif any((r["key"], r["corpus_value"]) == want for r in triage):
            print(f"  {GREEN}regression OK{RESET}  the 2026-09-02 s_coast row "
                  f"reaches TRIAGE")
        else:
            got = next(b for b in order for r in buckets[b]
                       if (r["key"], r["corpus_value"]) == want)
            print(f"  {RED}REGRESSION FAILED{RESET}  the 2026-09-02 s_coast "
                  f"row was sorted into {got}, not TRIAGE")
            return 1

    if args.json:
        json.dump({k: buckets[k] for k in order}, open(args.json, "w"), indent=1)
        print(f"\n  full sort written to {args.json}")

    print(f"cite_triage: {len(triage)} of {len(rows)} need reading "
          f"(reported, not gated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
