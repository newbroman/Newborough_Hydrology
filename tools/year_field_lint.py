#!/usr/bin/env python3
"""year_field_lint.py — a citation of Martin's own work prints its year from a field, not as typed text (D-341, draft).

WHY
  "Hollingham (2026d)" is the year a work is expected to appear, and the works will not all appear in 2026
  (Martin, 2026-11-24: "by the time I publish all these docs will be dated 2027"). src/utils/publication.py holds
  one year per work; tools/number_fields.csv binds each citation to it, so a change of year is one edit and
  `field_sync --write`. This gate stops the typed form from regrowing: every live document's count of BARE
  self-citation years (a year after "Hollingham" in a reference or citation, outside any field; Martin 2026-11-24:
  "only … 2026 in references with Hollingham, written before hand", and "the two by lines will need updating too";
  never the record's dates) may not exceed its frozen
  inventory, `tools/year_field_inventory.csv`. The held documents (Paper 1 and Paper C families, 2026-11-24) carry
  their counts there until they are bound; a count that FALLS is reported so the inventory can be lowered.

  Out of reach by design: other authors' years, dated history, the years of the record, imagery and surveys.
  Those are facts (working/updates/year_audit_2026-11-24/YEAR_FIELDS_PROPOSAL.md (private), the census of 2026-11-24).

    python3 tools/year_field_lint.py               # report every document's count against its inventory
    python3 tools/year_field_lint.py --check       # exit 1 if any document has more bare years than its inventory
    python3 tools/year_field_lint.py --freeze      # write the inventory from the documents as they stand
    python3 tools/year_field_lint.py --selftest
"""
from __future__ import annotations

__version__ = "1.0.1"  # Hollingham (2026) — 2026-11-24. Martin: "we should only be changing 2026 in references with
#   Hollingham, written before hand" and "the two by lines will need updating too": a year after "Hollingham" in a
#   reference or citation, and the year under "M. Hollingham" in a byline, count; a record date ("by early 2026") never.
# 1.0.0  # Hollingham (2026) — 2026-11-24. New (D-341 draft).

import argparse
import csv
import html
import pathlib
import re
import sys
import zipfile

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
INVENTORY = REPO / "tools" / "year_field_inventory.csv"
MIRRORS = ("report_edits/text/report*.md", "docs/report/text/*.md", "docs/papers/*/text/*.md")

FIELD = re.compile(r"<text:user-field-get\b.*?</text:user-field-get>", re.S)
PARA = re.compile(r"<text:(p|h)\b[^>]*?(?<!/)>(.*?)</text:\1>", re.S)
# A year after "Hollingham" in any citation style the corpus uses: (Hollingham, 2026a), Hollingham (2026d),
# Hollingham, M. (2026c), Hollingham, M., 2026e. — and a byline: "M. Hollingham" then the year, or "Draft — 2026".
CITE = re.compile(r"Hollingham(?:,? M\.,?)?\s*[(,]?\s*(?:\d{4}[a-h]?,\s*)*(20\d\d)(?![\d-])")
BYLINE = re.compile(r"^(?:Draft\s*[—-]\s*)?(20\d\d)$")
# The report's issue line in a reference entry: "Technical report, October 2026." (the month stays typed text).
ISSUE = re.compile(r"Technical report, (?:January|February|March|April|May|June|July|August|September|October|November|December) (20\d\d)(?!\d)")


def bare_years(xml: str) -> int:
    """Self-citation and byline years outside any field, in a document's content.xml."""
    x = FIELD.sub("⟨F⟩", xml)
    n, prev = 0, ""
    for m in PARA.finditer(x):
        t = html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        n += len(CITE.findall(t)) + len(ISSUE.findall(t))
        if BYLINE.match(t) and prev.endswith("M. Hollingham"):
            n += 1
        prev = t
    return n


def live_documents() -> dict[str, pathlib.Path]:
    import field_convert as fc
    out = {}
    for pat in MIRRORS:
        for md in sorted(REPO.glob(pat)):
            if md.stem == "style_donor":
                continue
            try:
                src, _ = fc.doc_for(md.stem)
            except Exception:
                continue
            if src is not None and src.exists() and src.suffix == ".odt":
                out[md.stem] = src
    return out


def counts() -> dict[str, int]:
    return {s: bare_years(zipfile.ZipFile(p).read("content.xml").decode("utf-8")) for s, p in live_documents().items()}


def load_inventory() -> dict[str, int]:
    if not INVENTORY.exists():
        return {}
    with open(INVENTORY, newline="", encoding="utf-8") as fh:
        return {r["document"]: int(r["bare_years"]) for r in csv.DictReader(fh)}


def selftest() -> int:
    ok = True
    def check(name, cond):
        nonlocal ok
        print(("  ok    " if cond else "  FAIL  ") + name); ok &= bool(cond)
    p = lambda s: f"<text:p>{s}</text:p>"
    f = '<text:user-field-get text:name="PUB_YEAR_REPORT_dp0">2026</text:user-field-get>'
    check("a bare citation counts", bare_years(p("as shown (Hollingham, 2026d).")) == 1)
    check("each citation style counts", bare_years(p("Hollingham (2026a); Hollingham, M. (2026b) T; Hollingham, M., 2026c. T")) == 3)
    check("a field does not count", bare_years(p(f"as shown (Hollingham, {f}d).")) == 0)
    check("another author's year does not count", bare_years(p("tide levels (UKHO, 2026).")) == 0)
    check("a date does not count", bare_years(p("Added 2026-07-18; Hollingham 2026-08-01 note")) == 0)
    check("a byline year under M. Hollingham counts", bare_years(p("M. Hollingham") + p("2026")) == 1)
    check("a draft byline under M. Hollingham counts", bare_years(p("M. Hollingham") + p("Draft — 2026")) == 1)
    check("a byline field does not count", bare_years(p("M. Hollingham") + p(f)) == 0)
    check("a record date does not count", bare_years(p("by early 2026 the CUSUM")) == 0)
    check("a lone year elsewhere does not count", bare_years(p("Results") + p("2026")) == 0)
    check("the report issue line counts", bare_years(p("Aquifer, Wales. Technical report, October 2026. https://x")) == 1)
    print("year_field_lint selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    now = counts()
    if a.freeze:
        with open(INVENTORY, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["document", "bare_years"])
            for s in sorted(now):
                w.writerow([s, now[s]])
        print(f"year_field_lint: inventory written - {sum(now.values())} bare year(s) in {sum(1 for v in now.values() if v)} document(s)")
        return 0
    inv = load_inventory()
    over = {s: (n, inv.get(s, 0)) for s, n in now.items() if n > inv.get(s, 0)}
    under = {s: (n, inv[s]) for s, n in now.items() if s in inv and n < inv[s]}
    for s, (n, k) in sorted(over.items()):
        print(f"  FAIL  {s}: {n} bare self-citation year(s), inventory {k} - bind the new one(s) to src/utils/publication.py")
    for s, (n, k) in sorted(under.items()):
        print(f"  note  {s}: {n} bare year(s), inventory {k} - lower the inventory (--freeze)")
    held = sum(n for n in now.values())
    if over:
        print(f"year_field_lint: FAIL - {len(over)} document(s) over their inventory")
        return 1 if a.check else 0
    print(f"year_field_lint: OK - no new bare self-citation year; {held} held in the inventory")
    return 0


if __name__ == "__main__":
    sys.exit(main())
