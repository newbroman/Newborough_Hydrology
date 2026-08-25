#!/usr/bin/env python3
"""symbol_inventory — every symbol the corpus actually uses, with a definition.

WHY

  tools/symbol_register.csv is a COLLISION register: eight glyphs that were
  found to carry more than one sense. It was never a nomenclature, and the
  Methods Supplement has no notation table, so most of the study's symbols are
  defined nowhere but in the sentence that first uses them - if there.

  On 2026-08-25 the Supplement alone used fifteen Greek glyphs; the register
  covered four. Unregistered and load-bearing: delta_0 (the coastal-gradient
  anchor, 59 uses), tau = Sy/beta_3 (the storage-drainage index, 37), and a
  bare gamma competing with gamma_P and gamma_S in the panel model.

WHAT IT DOES

  Sweeps the mirrors for symbol-shaped tokens, counts them per document, and
  for each one proposes the sentence most likely to be its definition. It fills
  in nothing it cannot see: `meaning` and `units` are left blank for a person,
  which is the point - the inventory is the worklist, not the answer.

  `pipeline_key` is filled where the symbol's value is a committed pipeline
  quantity, so cite_check can eventually check a symbol's stated value the way
  it checks a citation.

HOW A DEFINITION IS RECOGNISED

  Not by proximity. "beta_1 is 4.58" is a value, not a definition. The patterns
  are the ones prose actually uses to introduce notation - "where X is", "X
  denotes", "X, the ...", "X (units)" - scored, with the highest-scoring
  sentence kept and its score reported so a weak guess is visible as one.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-25. First issue.

import csv, re, pathlib, collections, argparse

REPO = pathlib.Path(__file__).resolve().parents[1]
DOCS = ["report_edits/text/report*.md", "docs/**/text/*.md",
        "PIPELINE_README.md", "readme.md"]

GREEK = "αβγδεζηθικλμνξοπρστυφχψωΓΔΘΛΞΠΣΦΨΩ"
SUB   = "₀₁₂₃₄₅₆₇₈₉ₐₑₒₓₕₖₗₘₙₚₛₜ"

# A symbol is a Greek letter, or a single Latin letter, optionally carrying a
# subscript in either of the two styles the corpus uses (unicode for digits,
# underscore for words). Bare single Latin letters are far too noisy to sweep,
# so they are admitted only WITH a subscript.
TOKEN = re.compile(
    rf"(?<![A-Za-z0-9_])("
    rf"[{GREEK}][{SUB}]*(?:_[A-Za-z][A-Za-z0-9]{{0,10}})?"
    rf"|[A-Za-z][{SUB}]+(?:_[A-Za-z][A-Za-z0-9]{{0,10}})?"
    rf"|[A-Za-z]_[A-Za-z][A-Za-z0-9]{{0,10}}"
    rf")(?![A-Za-z0-9_])")

# Words that mean the sentence is introducing notation rather than using it.
DEFINING = [
    (r"\bwhere\b",                     3),
    (r"\bdenotes?\b",                  4),
    (r"\bis the\b",                    3),
    (r"\bare the\b",                   3),
    (r"\bdefined as\b",                4),
    (r"\bwritten\b",                   2),
    (r"\bexpressed as\b",              3),
    (r"\bthe .{0,30}coefficient\b",    2),
    (r"\(m|\(mm|\(month|\(dimensionless|\(m³|\(m2|\(m yr", 2),
]
SENT = re.compile(r"(?<=[.;])\s+")


def sentences(text: str):
    for para in text.split("\n"):
        if not para.strip():
            continue
        for s in SENT.split(para):
            s = s.strip()
            if 20 < len(s) < 700:
                yield s


def score(sentence: str, tok: str) -> int:
    s = 0
    for pat, w in DEFINING:
        if re.search(pat, sentence, re.I):
            s += w
    # "where X is" adjacency is worth more than the words appearing anywhere
    if re.search(r"where\s+\**" + re.escape(tok), sentence, re.I):
        s += 4
    if re.search(re.escape(tok) + r"\s*(?:is|denotes|=)\b", sentence):
        s += 3
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-count", type=int, default=3)
    ap.add_argument("--out", default="tools/symbol_inventory_draft.csv")
    a = ap.parse_args()

    files = []
    for g in DOCS:
        files += [p for p in REPO.glob(g) if p.is_file()]
    files = sorted(set(files))

    per_doc = collections.defaultdict(collections.Counter)
    best = {}
    for p in files:
        t = p.read_text(encoding="utf-8", errors="replace")
        rel = p.relative_to(REPO).as_posix()
        for m in TOKEN.finditer(t):
            per_doc[m.group(1)][rel] += 1
        for s in sentences(t):
            for tok in set(TOKEN.findall(s)):
                sc = score(s, tok)
                if sc and sc > best.get(tok, (0, "", ""))[0]:
                    best[tok] = (sc, s[:300], rel)

    rows = []
    for tok, docs in sorted(per_doc.items(), key=lambda kv: -sum(kv[1].values())):
        n = sum(docs.values())
        if n < a.min_count:
            continue
        sc, sent, where = best.get(tok, (0, "", ""))
        rows.append({
            "symbol": tok, "uses": n, "documents": len(docs),
            "top_document": docs.most_common(1)[0][0],
            "meaning": "", "units": "", "pipeline_key": "",
            "definition_score": sc,
            "candidate_definition": sent,
            "definition_seen_in": where,
        })

    out = REPO / a.out
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    undef = sum(1 for r in rows if r["definition_score"] == 0)
    print(f"  {len(rows)} symbol(s) at >= {a.min_count} uses across {len(files)} documents")
    print(f"  {len(rows)-undef} have a candidate definition; {undef} have none at all")
    print(f"  -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
