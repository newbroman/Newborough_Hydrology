#!/usr/bin/env python3
"""
section_map.py — the numbered section backbone, read from the ODTs.

WHY

  Section numbers are ODF outline numbering. They exist in the rendered document
  and nowhere in the markdown mirrors: a mirror shows `## Network Clustering and
  Spatial Architecture` with no number at all. Every "Section 4.6" in the corpus
  is therefore a HAND-TYPED string with nothing checking it, and inserting or
  cutting a section silently invalidates every reference after it.

  That is not a hypothetical. A new §4.10 "Coastal erosion and the cross-shore
  section" has been designed and approved, and it moves Scenario Analysis to
  §4.11 — which re-points every typed §4.10.x reference in the Discussion,
  Limitations and Conclusions. Those are typed text, not fields, because
  cross-reference fields cannot span sub-documents in an ODF master.

  This tool makes the backbone addressable so that renumber is a mechanical list
  rather than a hunt. It is the same trick `reference_lint` uses for table
  captions — read the resolved value out of the ODT rather than the mirror — and
  it is the prerequisite the traceability specification names for keying any
  register to a section.

HOW

  Headings are `<text:h text:outline-level="N">` in document order. Chapter
  number = position of the sub-document in report.odm's section-source list
  (report6 = 1 ... report9 = 4 ... report15 = 10), which is why report9's prose
  self-references run 4.x and report10's run 5.x. Section number = a positional
  counter at each outline level, reset whenever a shallower level advances.

  GENERATED, NEVER HAND-EDITED. Emitted alongside the mirrors so map and mirror
  cannot diverge.

WHAT IT DOES NOT KNOW

  Whether LibreOffice's own numbering skips a heading whose paragraph style is
  outline-unnumbered. The generator flags any heading whose text already begins
  with a digit-dotted prefix ("4.1.2 Well Network"), because a hand-typed number
  inside heading text will lie after any renumber and is the most likely source
  of a mismatch. Validate the map once against the exported PDF's headings before
  trusting it for a renumber.

Usage:
    python3 tools/section_map.py                 # write tools/section_map.csv
    python3 tools/section_map.py --print         # show the map
    python3 tools/section_map.py --check-refs    # typed Section X.Y that do not resolve
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-23.

import argparse
import csv
import re
import sys
import zipfile
from pathlib import Path
from doc_paths import MASTER_ODM, ODT_DIR as _ODT_DIR

REPO = Path(__file__).resolve().parents[1]
MASTER = MASTER_ODM
ODT_DIR = _ODT_DIR
OUT = Path(__file__).resolve().parent / "section_map.csv"

_H = re.compile(r'<text:h\b([^>]*)>(.*?)</text:h>', re.S)
_LEVEL = re.compile(r'text:outline-level="(\d+)"')
_TAG = re.compile(r"<[^>]+>")
_NUMBERED_PREFIX = re.compile(r"^\s*\d+(?:\.\d+)*\s")


def master_order() -> list[str]:
    x = zipfile.ZipFile(MASTER).read("content.xml").decode("utf-8")
    seen, out = set(), []
    for m in re.finditer(r'xlink:href="[^"]*?(report\d+)\.odt"', x):
        if m.group(1) not in seen:
            seen.add(m.group(1)); out.append(m.group(1))
    return out


def headings(odt: Path) -> list[tuple[int, str]]:
    """[(outline_level, text)] in document order. Tags stripped with NOTHING
    between them — LibreOffice splits runs mid-word, so a space would break
    'Clearfell' into two tokens."""
    x = zipfile.ZipFile(odt).read("content.xml").decode("utf-8")
    out = []
    for m in _H.finditer(x):
        lvl = _LEVEL.search(m.group(1))
        if not lvl:
            continue
        txt = _TAG.sub("", m.group(2))
        txt = txt.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        txt = " ".join(txt.split())
        if txt:
            out.append((int(lvl.group(1)), txt))
    return out


def build() -> list[dict]:
    rows, order = [], master_order()
    for chapter, stem in enumerate(order, start=1):
        odt = ODT_DIR / f"{stem}.odt"
        if not odt.exists():
            continue
        counters: dict[int, int] = {}
        for lvl, txt in headings(odt):
            counters[lvl] = counters.get(lvl, 0) + 1
            for deeper in [k for k in counters if k > lvl]:
                del counters[deeper]
            parts = [str(chapter)] + [str(counters[k])
                                      for k in sorted(counters) if k > 1]
            number = ".".join(parts) if lvl > 1 else str(chapter)
            rows.append({
                "document": f"{stem}.odt",
                "chapter": chapter,
                "level": lvl,
                "number": number,
                "heading": txt,
                "typed_prefix": "yes" if _NUMBERED_PREFIX.match(txt) else "",
            })
    return rows


_REF = re.compile(r"(?i)\bsection\s+(\d+(?:\.\d+){0,3})")


def check_refs(rows: list[dict]) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import cite_check as cc
    valid = {r["number"] for r in rows}
    bad, total = {}, 0
    for doc, text in cc.load_documents().items():
        for m in _REF.finditer(text):
            total += 1
            n = m.group(1)
            if n not in valid:
                bad.setdefault(n, []).append(doc)
    print(f"  {total} typed 'Section N' reference(s) across the corpus")
    if not bad:
        print("  every typed section reference resolves against the map")
        return 0
    print(f"  {len(bad)} distinct reference(s) do NOT resolve:")
    for n in sorted(bad, key=lambda s: [int(p) for p in s.split(".")]):
        docs = sorted({Path(d).name for d in bad[n]})
        print(f"      Section {n:<10} cited in {len(bad[n])} place(s): {', '.join(docs)}")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", dest="show", action="store_true")
    ap.add_argument("--check-refs", action="store_true")
    args = ap.parse_args()

    rows = build()
    with OUT.open("w", newline="", encoding="utf8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader(); wr.writerows(rows)
    print(f"  {len(rows)} heading(s) mapped across {len({r['document'] for r in rows})} "
          f"sub-document(s) -> {OUT.name}")
    flagged = [r for r in rows if r["typed_prefix"]]
    if flagged:
        print(f"  {len(flagged)} heading(s) carry a hand-typed number in the text "
              f"and will lie after any renumber:")
        for r in flagged:
            print(f"      {r['number']:<10} {r['heading'][:64]}")
    if args.show:
        for r in rows:
            if r["level"] <= 2:
                print(f"    {r['number']:<8} {'  ' * (r['level'] - 1)}{r['heading'][:70]}")
    if args.check_refs:
        return check_refs(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
