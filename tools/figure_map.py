#!/usr/bin/env python3
"""
figure_map.py — every figure's rendered number, and the section it sits in.

WHY

  Figure numbers are ODF sequence fields: they render correctly and they exist
  nowhere in the markdown mirrors. Every "Figure 52" in the corpus is a
  HAND-TYPED string. There are 518 of them.

  The report is about to gain a new §4.10 assembled by RELOCATION — the coastal
  material now split across §4.8 and §4.9.4 moves into one section. That moves
  Figures 41, 42 and 52-56 and shifts 43-68 by seven, putting **234 typed figure
  references and up to 155 typed section references in play**. Hand-editing 389
  cross-references is how a wrong one reaches a submitted paper.

  This tool is the before-state that makes the move mechanical: it says what
  every figure's number is today and which section owns it, so the after-state
  can be computed rather than counted by eye.

HOW

  The sub-document caption sequences restart per file ("1.1" ... "1.66"), so a
  caption's own text is NOT the rendered number. The rendered number is the
  cumulative position of the sequence field across report.odm's section-source
  order. Verified: report7 = 1-2, report8 = 3, report9 = 4-69, report10 = 70-74,
  total 74 — which matches the highest typed reference in the corpus exactly,
  and matches the author's own count of five figures in the Discussion.

  Panel captions ("Figure 1.1a" / "1.1b") share one sequence field and therefore
  one number; report9 carries 77 caption paragraphs against 66 sequence fields
  for exactly this reason. The sequence field is the authority.

Usage:
    python3 tools/figure_map.py              # write tools/figure_map.csv
    python3 tools/figure_map.py --print      # number, section, caption
    python3 tools/figure_map.py --refs       # typed references per figure number
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-23.

import argparse
import collections
import csv
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import section_map as sm                                    # noqa: E402

REPO = sm.REPO
OUT = Path(__file__).resolve().parent / "figure_map.csv"

_TAG = re.compile(r"<[^>]+>")
_H = re.compile(r'<text:h\b([^>]*)>(.*?)</text:h>', re.S)
_LEVEL = re.compile(r'text:outline-level="(\d+)"')
_SEQ = re.compile(r'<text:sequence[^>]*text:name="Figure"[^>]*>([^<]*)</text:sequence>')
_CAP = re.compile(r'<text:p[^>]*>((?:(?!</text:p>).)*)</text:p>', re.S)


def _clean(s: str) -> str:
    s = _TAG.sub("", s)
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return " ".join(s.split())


def build() -> list[dict]:
    rows, n = [], 0
    for chapter, stem in enumerate(sm.master_order(), start=1):
        odt = sm.ODT_DIR / f"{stem}.odt"
        if not odt.exists():
            continue
        x = zipfile.ZipFile(odt).read("content.xml").decode("utf-8")
        events = []
        for m in _H.finditer(x):
            lvl = _LEVEL.search(m.group(1))
            t = _clean(m.group(2))
            if lvl and t:
                events.append((m.start(), "H", int(lvl.group(1)), t))
        for m in _SEQ.finditer(x):
            # the caption paragraph this sequence field sits in
            p0 = x.rfind("<text:p", 0, m.start())
            p1 = x.find("</text:p>", m.start())
            cap = _clean(x[p0:p1]) if p0 >= 0 and p1 > p0 else ""
            events.append((m.start(), "F", 0, cap))
        events.sort()
        counters: dict[int, int] = {}
        sec_no, sec_txt = str(chapter), ""
        for _, kind, lvl, txt in events:
            if kind == "H":
                counters[lvl] = counters.get(lvl, 0) + 1
                for deeper in [k for k in counters if k > lvl]:
                    del counters[deeper]
                parts = [str(chapter)] + [str(counters[k]) for k in sorted(counters) if k > 1]
                sec_no = ".".join(parts) if lvl > 1 else str(chapter)
                sec_txt = txt
            else:
                n += 1
                rows.append({"number": n, "document": f"{stem}.odt",
                             "section": sec_no, "section_heading": sec_txt,
                             "caption": txt[:110]})
    return rows


def typed_refs() -> collections.Counter:
    import cite_check as cc
    c = collections.Counter()
    for _, t in cc.load_documents().items():
        for m in re.finditer(r"(?i)\bfigures?\s+(\d{1,3})\b", t):
            c[int(m.group(1))] += 1
    return c


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", dest="show", action="store_true")
    ap.add_argument("--refs", action="store_true")
    args = ap.parse_args()

    rows = build()
    with OUT.open("w", newline="", encoding="utf8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader(); wr.writerows(rows)
    per_doc = collections.Counter(r["document"] for r in rows)
    print(f"  {len(rows)} figure(s) mapped -> {OUT.name}")
    for d, k in per_doc.items():
        first = next(r["number"] for r in rows if r["document"] == d)
        print(f"      {d:<14} {k:>3} figure(s)   global {first}-{first + k - 1}")

    if args.show:
        for r in rows:
            print(f"    {r['number']:>3}  §{r['section']:<8} {r['caption'][:78]}")

    if args.refs:
        c = typed_refs()
        unmapped = [n for n in sorted(c) if n > len(rows)]
        print(f"\n  {sum(c.values())} typed 'Figure N' reference(s); "
              f"highest is {max(c)} against {len(rows)} mapped figure(s)")
        if unmapped:
            print(f"  references above the map: {unmapped}")
        else:
            print("  every typed reference falls inside the map")
        by_sec = collections.defaultdict(int)
        for r in rows:
            by_sec[r["section"]] += c.get(r["number"], 0)
        print("\n  typed references by owning section (top 12):")
        for s, k in sorted(by_sec.items(), key=lambda kv: -kv[1])[:12]:
            print(f"      §{s:<10} {k:>4}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
