#!/usr/bin/env python3
"""Check inequality-form significance claims against the committed outputs (T15b).

THE GAP THIS CLOSES. Every numeric check in this project matches a NUMBER in a
document against a number in a CSV. "p < 0.001" carries no number to match, so
it is invisible to all of them. That is not hypothetical: the +113 mm clearfell
step is committed at p = 0.0021 and the academic summaries state p < 0.001 for
it — false, and no tool could have seen it.

The register is the answer, not the number path: an inequality is a CLAIM about
a committed value, so it belongs beside the other claims that carry no number of
their own.

HOW IT WORKS. `tools/inequality_claims.csv` binds one occurrence to one committed
value:

    claim_id      short name
    doc           mirror path the claim appears in
    context       literal text that must appear EXACTLY ONCE in that doc, and
                  must itself contain the inequality (so a reworded sentence
                  fails loudly instead of silently checking nothing)
    csv           committed output the value comes from
    key_col,key   which row
    value_from    a column name, or `note_p` to read `p=<number>` out of Note
    relation      lt | le  (the claim's own operator)
    threshold     the number the claim asserts the value is below

A registered claim is BREACH when the committed value does not satisfy it.
Unregistered occurrences are counted and listed as a backlog: they are advisory,
deliberately, because there are ~94 of them across the corpus and a gate nobody
can pass is a gate that gets switched off. Register the ones that carry a
headline; the count keeps the rest visible.

Usage:
    python3 tools/inequality_lint.py              # check, exit 1 on BREACH/FAULT
    python3 tools/inequality_lint.py --backlog    # also list unregistered ones
    python3 tools/inequality_lint.py --selftest   # prove the checker detects a lie
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-09. First version (T15b).

import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REGISTER = REPO / "tools" / "inequality_claims.csv"

DOC_GLOBS = ["report_edits/text/*.md", "docs/*/text/*.md", "docs/*/*/text/*.md"]

# Pandoc escapes "<" as "\<" in the mirrors, so both forms must match. The
# trailing boundary stops "0.05" matching inside "0.055".
INEQ = re.compile(r"[pP]\s*\\?[<≤]\s*(0?\.\d+)(?![\d])|\(\s*\\?[<≤]\s*(0?\.\d+)\s*\)")


def docs() -> dict[str, str]:
    out = {}
    for g in DOC_GLOBS:
        for p in sorted(REPO.glob(g)):
            out[str(p.relative_to(REPO))] = p.read_text(encoding="utf-8")
    return out


def occurrences(text: str) -> list[str]:
    return [m.group(0) for m in INEQ.finditer(text)]


def committed(row: dict) -> tuple[float | None, str]:
    """The value this claim is about, from the committed CSV."""
    path = REPO / row["csv"]
    if not path.exists():
        return None, f"{row['csv']} missing"
    import pandas as pd
    df = pd.read_csv(path)
    key_col = row["key_col"]
    if key_col not in df.columns:
        return None, f"no column {key_col!r} in {row['csv']}"
    hit = df[df[key_col].astype(str).str.strip() == row["key"].strip()]
    if len(hit) != 1:
        return None, f"{key_col} == {row['key']!r} selects {len(hit)} row(s), needs 1"
    src = row["value_from"].strip()
    if src == "note_p":
        note = str(hit.iloc[0].get("Note", ""))
        m = re.search(r"\bp\s*=\s*([0-9.]+)", note)
        if not m:
            return None, f"no 'p=<number>' in the Note of {row['key']}"
        return float(m.group(1)), f"Note p={m.group(1)}"
    if src not in df.columns:
        return None, f"no column {src!r} in {row['csv']}"
    return float(hit.iloc[0][src]), f"{src}={hit.iloc[0][src]}"


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        # A checker that cannot fail proves nothing. Assert the comparison
        # rejects the exact class of claim this tool exists to catch.
        ok = (not _satisfies(0.0021, "lt", 0.001)) and _satisfies(0.0021, "lt", 0.01)
        print("  selftest:", "OK" if ok else "FAILED")
        return 0 if ok else 1

    corpus = docs()
    if not REGISTER.exists():
        print(f"  FAULT  {REGISTER.relative_to(REPO)} missing")
        return 1

    rows = list(csv.DictReader(REGISTER.open(encoding="utf-8")))
    bad = 0
    registered_ctx: set[tuple[str, str]] = set()

    for row in rows:
        cid, doc, ctx = row["claim_id"], row["doc"], row["context"]
        text = corpus.get(doc)
        if text is None:
            print(f"  FAULT  {cid}: {doc} is not in the corpus — NOT CHECKED")
            bad += 1
            continue
        n = text.count(ctx)
        if n != 1:
            print(f"  FAULT  {cid}: context found {n}x in {doc}, needs exactly 1 "
                  f"— the sentence changed; re-point the register")
            bad += 1
            continue
        if not INEQ.search(ctx):
            print(f"  FAULT  {cid}: the registered context carries no inequality "
                  f"— it would check nothing")
            bad += 1
            continue
        registered_ctx.add((doc, ctx))

        val, how = committed(row)
        if val is None:
            print(f"  FAULT  {cid}: {how} — NOT CHECKED")
            bad += 1
            continue
        thr = float(row["threshold"])
        if _satisfies(val, row["relation"], thr):
            print(f"  HOLDS  {cid}: {how} satisfies {row['relation']} {thr}")
        else:
            op = "<" if row["relation"] == "lt" else "≤"
            print(f"  BREACH {cid}: the document claims p {op} {thr}, "
                  f"the committed value is {val} ({how})")
            print(f"          {doc}: ...{ctx.strip()[:100]}...")
            bad += 1

    # Backlog: occurrences the register does not cover.
    total = sum(len(occurrences(t)) for t in corpus.values())
    print(f"\n  {len(rows)} registered claim(s); {total} inequality-form statement(s) "
          f"in the corpus")
    if "--backlog" in argv:
        for doc, text in sorted(corpus.items()):
            for m in INEQ.finditer(text):
                s = max(0, m.start() - 70)
                frag = " ".join(text[s:m.end() + 20].split())
                if not any(c in frag for d, c in registered_ctx if d == doc):
                    print(f"    {doc}: ...{frag}")

    print(f"\ninequality_lint: {'OK' if bad == 0 else 'FAIL'}")
    return 1 if bad else 0


def _satisfies(value: float, relation: str, threshold: float) -> bool:
    return value < threshold if relation == "lt" else value <= threshold


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
