#!/usr/bin/env python3
"""
pdf_page_index.py — which page of the published PDF each paragraph, heading, figure
and table of a mirror sits on, so the proof copy can link a number to the page
it is printed on.

WHY
  Martin, 2026-09-20: "Would it be possible to link the proof reading tool to the
  relevant parts of the pdfs?" The proof copy paints the MIRROR (the pandoc text of
  the ODT); the reader also has the PDF, and a browser opens a PDF at a page with
  `report.pdf#page=N`. This maps mirror -> page by matching text, once per PDF,
  and the proof copy attaches the page to every span.

HOW
  pdftotext (poppler) gives one form-feed-separated text per page. Every string is
  reduced to lowercase alphanumerics before comparison, so hyphenation, ligatures,
  dash glyphs and markdown escapes all drop out. A paragraph is keyed by the first
  FINGERPRINT alphanumerics of its text; a figure by its caption's first words after
  "Figure N:"; a table likewise; a heading takes the page of its first paragraph
  (the heading text alone would match the table of contents). Where a fingerprint
  matches several pages the LAST match is taken — the body follows the lists of
  figures and tables — and the ambiguity is recorded.

WHAT IT WRITES
  tools/pdf_page_index.csv: document, kind (para|heading|figure|table), key, page,
  pdf, pdf_built (the PDF's mtime, UTC). Regenerate after every PDF build; the proof
  copy reads it and says which build the pages belong to.

Usage:
    python3 tools/pdf_page_index.py            # every mirror that has a published PDF
    python3 tools/pdf_page_index.py --only report
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) — 2026-09-21. A caption is fingerprinted from its
#   body — the mirror renders an unfilled sequence field as "Table :" while the PDF
#   says "Table 12:", so every caption read as absent — and a block carrying display
#   maths is not fingerprinted at all (pdftotext lays equations out differently, and
#   a miss there says nothing about the PDF). para_key() is shared with proof_copy so
#   the two tools cannot fingerprint differently. Martin, 2026-09-21: "a lot of the
#   red notes are p?" — 77 of 88 were equations, captions and one-line sub-headings.
#   --only now keeps the other documents' rows instead of dropping them.
# 1.0.0  # Hollingham (2026) — 2026-09-20.

import argparse
import csv
import datetime as dt
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
OUT = REPO / "tools" / "pdf_page_index.csv"
FIG_MAP = REPO / "tools" / "figure_map.csv"
TAB_MAP = REPO / "tools" / "reference_index_table.csv"
FINGERPRINT = 60

# mirror -> published PDF. The report chapters share the master's PDF.
PDF_OF = {
    "report": "docs/report/report.pdf",
    **{f"report{n}": "docs/report/report.pdf" for n in range(6, 17)},
    "Paper1": "docs/papers/paper_1/Paper1.pdf",
    "PAPER1_SI_methods": "docs/papers/paper_1/PAPER1_SI_methods.pdf",
    "Newborough_Methods_Supplement": "docs/report/Newborough_Methods_Supplement.pdf",
    "Supplementary_Material": "docs/report/Supplementary_Material.pdf",
    "Hollingham_2026_Paper2_amended": "docs/papers/paper_2/Hollingham_2026_Paper2_amended.pdf",
    "academic_Summary": "docs/academic_summaries/academic_summary.pdf",
    "crynodeb_academaidd": "docs/academic_summaries/crynodeb_academaidd.pdf",
    "public_summary_EN": "docs/public_summaries/Newborough_Warren_Public_Summary.pdf",
    "public_summary_CY": "docs/public_summaries/Niwbwrch_Crynodeb_Cyhoeddus.pdf",
    "public_summary_PL": "docs/public_summaries/Newborough_Warren_Podsumowanie.pdf",
    "NRG_Web_Tools_Technical_Note": "docs/web_tools/NRG_Web_Tools_Technical_Note.pdf",
    "NRG_Web_Tools_User_Manual": "docs/web_tools/NRG_Web_Tools_User_Manual.pdf",
}
MIRROR_GLOBS = ("report_edits/text/*.md", "docs/**/text/*.md")
_MARKUP = re.compile(r"!\[[^\]]*\]\([^)]*\)(\{[^}]*\})?|\[\]\{#[^}]*\}|\{[^}]*\}|\*\*|\\(.)")
_HEAD = re.compile(r"^(#{1,4})\s+(.*)$")


_CAPTION = re.compile(r"^\*?\s*(Table|Figure|Fig\.)\s*[\d.]*[a-z]?\s*:\s*", re.I)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def para_key(block: str) -> str:
    """The normalised text a paragraph is looked up by: markup stripped, a caption's
    "Table N:" label dropped (the mirror may render the field empty), lower-case
    alphanumerics only. "" for a block that cannot be matched (display maths)."""
    if "$$" in block:
        return ""
    clean = _MARKUP.sub(lambda m: m.group(2) or "", block)
    return norm(_CAPTION.sub("", clean.strip()))


def pdf_pages(pdf: pathlib.Path) -> list[str]:
    txt = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"],
                         capture_output=True, text=True, check=True).stdout
    return [norm(p) for p in txt.split("\f")]


def find_page(pages: list[str], key: str, after: int = 0) -> tuple[int, int]:
    """(1-based page, number of matching pages). The LAST match wins."""
    hits = [i for i, p in enumerate(pages) if i >= after and key and key in p]
    return (hits[-1] + 1 if hits else 0), len(hits)


def paragraphs(mirror: pathlib.Path):
    """(kind, key, fingerprint, heading-number) per block of the mirror."""
    out = []
    cur_head = ""
    for raw in mirror.read_text(encoding="utf8").split("\n\n"):
        block = raw.strip()
        if not block or block.startswith("<!--"):
            continue
        hm = _HEAD.match(block.split("\n")[0])
        if hm:
            cur_head = _MARKUP.sub(r"\2", hm.group(2)).strip()
            out.append(("heading", cur_head, "", ""))
            continue
        fp = para_key(block)[:FINGERPRINT]
        if len(fp) < 30:
            continue
        out.append(("para", fp[:24], fp, cur_head))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="substring of the mirror stem")
    a = ap.parse_args()
    figs = list(csv.DictReader(FIG_MAP.open(encoding="utf8"))) if FIG_MAP.exists() else []
    tabs = list(csv.DictReader(TAB_MAP.open(encoding="utf8"))) if TAB_MAP.exists() else []
    rows, cache = [], {}
    mirrors = sorted(p for g in MIRROR_GLOBS for p in REPO.glob(g))
    for mirror in mirrors:
        stem = mirror.stem
        if a.only and a.only.lower() not in stem.lower():
            continue
        rel = PDF_OF.get(stem)
        if not rel or not (REPO / rel).exists():
            continue
        pdf = REPO / rel
        if rel not in cache:
            cache[rel] = pdf_pages(pdf)
        pages = cache[rel]
        built = dt.datetime.utcfromtimestamp(pdf.stat().st_mtime).strftime("%Y-%m-%dT%H:%MZ")
        n_ok = n_amb = n_miss = 0
        pending_heads = []
        for kind, key, fp, head in paragraphs(mirror):
            if kind == "heading":
                pending_heads.append(key)
                continue
            page, n = find_page(pages, fp)
            if not page:
                n_miss += 1
                continue
            n_ok += 1
            n_amb += n > 1
            rows.append([stem, "para", key, page, rel, built, n])
            for h in pending_heads:                      # a heading sits where its first paragraph does
                rows.append([stem, "heading", h, page, rel, built, n])
            pending_heads = []
        # figures and tables: the caption, by its global number, in the report's PDF
        if rel.endswith("report.pdf") and stem == "report":
            for r in figs:
                cap = re.sub(r"^Figure\s+[\d.]+[a-z]?:\s*", "", r.get("caption") or "")
                key = norm(f"Figure {r['number']}:" + cap)[:FINGERPRINT]
                page, n = find_page(pages, key)
                if not page:                              # fall back to the caption words alone
                    page, n = find_page(pages, norm(cap)[:FINGERPRINT])
                if page:
                    rows.append([stem, "figure", r["number"], page, rel, built, n])
            for r in tabs:
                key = norm(f"Table {r['number']}:" + (r.get("title") or ""))[:FINGERPRINT]
                page, n = find_page(pages, key)
                if not page:
                    page, n = find_page(pages, norm(r.get("title") or "")[:FINGERPRINT])
                if page:
                    rows.append([stem, "table", r["number"], page, rel, built, n])
        print(f"  {stem:32} {pathlib.Path(rel).name:40} {len(pages):4} pages  "
              f"{n_ok} paragraph(s) placed, {n_amb} on more than one page, {n_miss} not found")
    if a.only and OUT.exists():
        # --only rebuilds the selected documents; the others keep their rows (1.0.0
        # rewrote the file with the selection alone and silently dropped the rest)
        done = {r[0] for r in rows}
        with OUT.open(encoding="utf8", newline="") as fh:
            kept = [r for r in csv.DictReader(fh) if r["document"] not in done]
        rows = [[r["document"], r["kind"], r["key"], r["page"], r["pdf"], r["pdf_built"], r["n_matches"]]
                for r in kept] + rows
    with OUT.open("w", encoding="utf8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["document", "kind", "key", "page", "pdf", "pdf_built", "n_matches"])
        w.writerows(rows)
    print(f"pdf_page_index {__version__}: {len(rows)} row(s) -> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
