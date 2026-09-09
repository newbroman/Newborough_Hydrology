#!/usr/bin/env python3
"""Check every typed pipeline count in the corpus against the committed manifest.

WHY THIS EXISTS. CLAUDE.md's first non-negotiable is that the pipeline step
count is derived and never hard-typed, and that documents quote
`outputs/pipeline_manifest.json`. On 2026-09-09 a sweep found the count typed in
NINE places across the corpus at FOUR different vintages:

    43   the Welsh academic summary
    52   the English academic summary, PIPELINE_README.md
    53   report8 §3.1, report12, report15, and the report.odm abstract
    54   the Methods Supplement, index.html   <- the manifest's actual value

Every one of those sentences ALSO told the reader that the canonical count lives
in the manifest. Knowing where the truth is has never been the problem; nothing
compared the two.

`sync_index_counts.py` already stamps the files that are plain text in the
repository (index.html, PIPELINE_README.md), so those cannot drift. This gate is
for the rest: the counts that live inside ODTs, which no script can rewrite
safely and which therefore have to be CHECKED instead.

HOW IT WORKS. `tools/pipeline_count_claims.csv` binds one occurrence to one
manifest field:

    claim_id   short name
    doc        mirror path the count appears in
    context    literal text that must appear EXACTLY ONCE in that doc, and must
               contain the number, so a reworded sentence fails loudly rather
               than silently checking nothing
    field      manifest key: total_registered | total_phases |
               by_tier.analytical_toplevel | by_tier.display_utility |
               by_tier.optin_diagnostic | by_exec.default | by_exec.optin

The number is read out of the context by position, so the register never repeats
it — there is no second copy of the count to go stale.

WHAT IT CANNOT CHECK. A count expressed as a RANGE of identifiers rather than a
number — "sub-scripts 10a-10n", which implies fourteen without writing it — has
no single number to read, and the exactly-one-number guard refuses it rather
than checking the wrong digits. The manifest carries `clearfell_substeps` and
`scraping_substeps`, so those two claims are real and unwatched; expressing them
would need a range mode, which is more machinery than two rows justify. They are
named here so the gap is recorded rather than assumed away.

Usage:
    python3 tools/pipeline_count_lint.py            # check, exit 1 on drift
    python3 tools/pipeline_count_lint.py --backlog  # unregistered count-like text
    python3 tools/pipeline_count_lint.py --selftest # prove it detects drift
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-09. First version.

import csv
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "outputs" / "pipeline_manifest.json"
REGISTER = REPO / "tools" / "pipeline_count_claims.csv"

# Documents that state a count in prose and cannot be stamped. index.html and
# PIPELINE_README.md are deliberately absent: sync_index_counts.py owns them.
DOC_GLOBS = ["report_edits/text/*.md", "docs/*/text/*.md", "docs/*/*/text/*.md"]

NUM = re.compile(r"\d+")


def manifest_value(field: str, m: dict):
    node = m
    for part in field.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def docs() -> dict[str, str]:
    out = {}
    for g in DOC_GLOBS:
        for p in sorted(REPO.glob(g)):
            out[str(p.relative_to(REPO))] = p.read_text(encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        m = {"total_registered": 54, "by_tier": {"analytical_toplevel": 43}}
        ok = (manifest_value("total_registered", m) == 54
              and manifest_value("by_tier.analytical_toplevel", m) == 43
              and manifest_value("by_tier.missing", m) is None
              and manifest_value("nope", m) is None
              and _numbers_in("a 54-step pipeline") == [54]
              and _numbers_in("53 steps across 17 phases") == [53, 17])
        print("  selftest:", "OK" if ok else "FAILED")
        return 0 if ok else 1

    if not MANIFEST.is_file():
        print(f"  FAULT  {MANIFEST.relative_to(REPO)} missing — run the pipeline")
        return 1
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    corpus = docs()

    if not REGISTER.is_file():
        print(f"  FAULT  {REGISTER.relative_to(REPO)} missing")
        return 1
    rows = list(csv.DictReader(REGISTER.open(encoding="utf-8")))
    if not rows:
        print("  0 registered count(s) — THIS GATE IS CHECKING NOTHING")
        return 1

    bad = 0
    for row in rows:
        cid, doc, ctx, field = row["claim_id"], row["doc"], row["context"], row["field"]
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
        stated = _numbers_in(ctx)
        if len(stated) != 1:
            print(f"  FAULT  {cid}: the registered context carries {len(stated)} numbers, "
                  f"needs exactly 1 — narrow it to the count being checked")
            bad += 1
            continue
        want = manifest_value(field, man)
        if want is None:
            print(f"  FAULT  {cid}: no manifest field {field!r}")
            bad += 1
            continue
        if stated[0] != want:
            print(f"  DRIFT  {cid}: {doc} says {stated[0]}, the manifest says {want} ({field})")
            print(f"          ...{ctx.strip()[:100]}...")
            bad += 1
        else:
            print(f"  ok     {cid}: {stated[0]} == manifest {field}")

    if "--backlog" in argv:
        print("\n  count-like statements not in the register:")
        pat = re.compile(r"[^.]{0,70}\b\d{1,3}[- ](?:registered )?(?:step|steps|cam|phase|phases)\b[^.]{0,40}")
        known = {(r["doc"], r["context"]) for r in rows}
        for doc, text in sorted(corpus.items()):
            for m in pat.finditer(text):
                frag = " ".join(m.group(0).split())
                if not any(c in frag for d, c in known if d == doc):
                    print(f"    {doc}: ...{frag}")

    print(f"\npipeline_count_lint: {'OK' if bad == 0 else 'FAIL'}")
    return 1 if bad else 0


def _numbers_in(s: str) -> list[int]:
    return [int(x) for x in NUM.findall(s)]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
