#!/usr/bin/env python3
"""
widen_probe.py — would matching documents against EVERY committed CSV cell make
the corpus traceable? Measured 2026-08-23. The answer is no, and this is kept so
the answer can be re-derived rather than re-argued.

  cell index          222,339 numeric cells -> 72,820 distinct rendering strings
  worst ambiguity     one rendering string is shared by 4,496 different labels
  effect on report9   2,143 unclassified -> 199 uniquely matched (9.3%)
  precision           ~1 in 10 of those "unique" matches survives adjudication

The failure is structural, not tunable. With 222k cells, a 3-significant-figure
number has many candidates, and the strict anchor passes on generic tokens — a
cluster id, or a word like "recharge", appears throughout the corpus. What comes
back is not a trace but a plausible candidate, which is worse than nothing
because it looks like an answer.

Kept as a probe, not wired into anything. Re-run it before proposing the
widening again.

    python3 tools/widen_probe.py
"""

import csv, glob, os, pathlib, sys, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cite_check as cc
import number_census as nc
from doc_paths import chapter_md

MAX_LABELS_TESTED = 40          # bound the anchor work; ambiguity is recorded exactly

def build_cells():
    ren = collections.defaultdict(list)
    ncells = 0
    for p in sorted(glob.glob("outputs/**/*.csv", recursive=True)):
        if any(d in p.split(os.sep) for d in cc.EXCLUDE_OUTPUT_DIRS):
            continue
        stem = os.path.basename(p)[:-4]
        try:
            with open(p, encoding="utf8", errors="ignore") as fh:
                rows = list(csv.reader(fh))
        except Exception:
            continue
        if len(rows) < 2:
            continue
        head = rows[0]
        for r in rows[1:]:
            if not r:
                continue
            rowkey = r[0].strip()
            for j in range(1, min(len(r), len(head))):
                c = r[j].strip()
                try:
                    v = float(c)
                except ValueError:
                    continue
                if not (abs(v) > 0):
                    continue
                ncells += 1
                label = f"{stem} {rowkey} {head[j]}"
                dps = [0, 2, 3, 4] if (v.is_integer() or abs(v) >= cc.LARGE_VALUE_MIN) else [2, 3, 4]
                for dp in dps:
                    s = cc.render(v, dp)
                    if cc.searchable(s, label):
                        ren[s.lstrip("+-−")].append(label)
    return ren, ncells


def measure(doc, text, ren, index):
    got = nc.classify(doc, text, {}, index)     # empty pipeline map: we want raw tokens
    unc = [(a, t) for a, t, c in got if c == "UNCLASSIFIED"]
    uniq = amb = none = 0
    amb_hist = collections.Counter()
    examples = {"unique": [], "ambiguous": []}
    for a, tok in unc:
        bare = tok.lstrip("+-−")
        cands = ren.get(bare) or ren.get(bare.replace(",", ""))
        if not cands:
            none += 1
            continue
        passed = []
        for lab in cands[:MAX_LABELS_TESTED]:
            if cc.anchored(text, tok, cc.anchors(lab), lab, strict=True):
                passed.append(lab)
                if len(passed) > 3:
                    break
        if not passed:
            none += 1
        elif len(passed) == 1:
            uniq += 1
            if len(examples["unique"]) < 12:
                examples["unique"].append((tok, passed[0],
                                           " ".join(text[max(0, a-60):a+len(tok)+40].split())))
        else:
            amb += 1
            amb_hist[min(len(passed), 4)] += 1
            if len(examples["ambiguous"]) < 8:
                examples["ambiguous"].append((tok, passed[:3],
                                              " ".join(text[max(0, a-60):a+len(tok)+40].split())))
    return len(unc), uniq, amb, none, amb_hist, examples


ren, ncells = build_cells()
print(f"cell index: {ncells} numeric cells -> {len(ren)} distinct rendering string(s)")
print(f"largest ambiguity in the index: "
      f"{max(len(v) for v in ren.values())} label(s) share one rendering\n")

docs = cc.load_documents()
index = nc._load_index()
TARGETS = [str(chapter_md(9)),
           "docs/report/text/Supplementary_Material.md",
           "docs/papers/paper_1/text/Paper1.md",
           "docs/papers/paper_2/text/Hollingham_2026_Paper2_amended.md"]
print(f"{'document':<46}{'unclass':>9}{'unique':>9}{'ambig':>8}{'still':>8}{'gain%':>8}")
print("-" * 88)
allex = {}
for d in TARGETS:
    if d not in docs:
        print("missing", d); continue
    n, u, a, z, hist, ex = measure(d, docs[d], ren, index.get(d, set()))
    allex[d] = (ex, hist)
    print(f"{os.path.basename(d):<46}{n:>9}{u:>9}{a:>8}{z:>8}{100.0*u/max(1,n):>7.1f}%")

for d, (ex, hist) in allex.items():
    print(f"\n=== {os.path.basename(d)} — uniquely matched, for adjudication ===")
    for tok, lab, ctx in ex["unique"][:10]:
        print(f"  {tok:>12}  <- {lab[:60]:<60}")
        print(f"                 ...{ctx[:120]}")
    if ex["ambiguous"]:
        print(f"  --- ambiguous (not a trace) ---  distribution {dict(hist)}")
        for tok, labs, ctx in ex["ambiguous"][:4]:
            print(f"  {tok:>12}  <- {len(labs)}+ candidates e.g. {labs[0][:50]} | {labs[1][:50]}")
