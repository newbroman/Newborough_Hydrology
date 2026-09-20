#!/usr/bin/env python3
"""
header_breaks.py — wrap table headers at "/", never mid-word.

THE PROBLEM

  A header cell narrower than its text is broken by LibreOffice wherever the
  line runs out, and a parenthesised unit is one "word" to the layout engine.
  Table 1.4b rendered like this in the 2026-09-19 export:

      Winter     Summer
      decline    decline    n months
      (mm/mo     (mm/mo     (winter/sum
      nth)       nth)       mer)

  "(mm/month)" broken as "(mm/mo" + "nth)" and "(winter/summer)" as
  "(winter/sum" + "mer)". Both should break after the slash.

THE FIX

  A zero-width space (U+200B) immediately after each "/" gives the engine a
  legal break there, which it prefers over an emergency mid-word break. It is
  invisible, it copies as nothing, and it is not a hyphen — nothing is added to
  the rendered text.

  Header cells only. Body cells carry values, and a value is table_gen's to
  write; a break opportunity inside a number would be a lie about the number.

  U+200B is stripped before table_gen compares a header against its config, so
  configs stay plain ASCII and this tool can run at any time.

Usage:
    python3 tools/header_breaks.py --check        # report, change nothing
    python3 tools/header_breaks.py --apply
    python3 tools/header_breaks.py --apply --doc report9
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-19.

import argparse
import pathlib
import re
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import odt_edit                                            # noqa: E402

ZWSP = "​"
REPO = pathlib.Path(__file__).resolve().parent.parent
CELL = re.compile(r"<table:table-cell\b.*?</table:table-cell>", re.S)
PARA = re.compile(r"(<text:p\b[^>]*>)(.*?)(</text:p>)", re.S)


def header_rows(xml: str):
    """(table_name, first-row XML) for every table, in document order."""
    for m in re.finditer(r'<table:table table:name="([^"]+)"[^>]*>', xml):
        end = xml.find("</table:table>", m.end())
        row = re.search(r"<table:table-row\b.*?</table:table-row>",
                        xml[m.end():end], re.S)
        if row:
            yield m.group(1), row.group(0)


def _text_only(inner: str) -> str:
    """Insert the break opportunity in TEXT nodes only, never inside a tag.

    The first version ran the substitution over the paragraph's whole inner XML.
    A self-closing tag ends in "/>", so it gained a zero-width space between the
    slash and the bracket and stopped being a tag — odt_edit's tag-sequence
    guard caught it on report9 and refused the write, which is exactly what that
    guard is for.
    """
    return "".join(part if part.startswith("<")
                   else re.sub(r"/(?!" + ZWSP + r")", "/" + ZWSP, part)
                   for part in re.split(r"(<[^>]*>)", inner))


def needed(row_xml: str) -> list[tuple[str, str]]:
    """[(old_cell_xml, new_cell_xml)] for header cells with an unbroken '/'."""
    out = []
    for cell in CELL.findall(row_xml):
        new = PARA.sub(lambda p: p.group(1) + _text_only(p.group(2)) + p.group(3),
                       cell)
        if new != cell:
            out.append((cell, new))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--doc", default=None, help="one document stem, e.g. report9")
    args = ap.parse_args()
    if not (args.apply or args.check):
        ap.error("choose --check or --apply")

    odts = sorted((REPO / "report_edits/odt").glob("report*.odt"))
    if args.doc:
        odts = [p for p in odts if p.stem == args.doc]
    rc = 0
    for path in odts:
        xml = zipfile.ZipFile(path).read("content.xml").decode("utf-8")
        subs, where = [], []
        for name, row in header_rows(xml):
            for old, new in needed(row):
                n = xml.count(old)
                if n != 1:                       # two identical header rows: skip,
                    continue                     # a counted sub cannot be honest
                subs.append((old, new, 1))
                where.append(name)
        if not subs:
            print(f"  ok      {path.name}: every header already breaks at '/'")
            continue
        rc = 1 if args.check else rc
        verb = "would fix" if args.check else "fixing  "
        print(f"  {verb} {path.name}: {len(subs)} header cell(s) in "
              f"{len(set(where))} table(s) — {', '.join(sorted(set(where)))}")
        if args.apply and not odt_edit.edit(path, path, subs, expect=len(subs)):
            rc = 1
    if args.check and rc:
        print("\nheader_breaks: header cell(s) can break mid-word — run --apply")
    else:
        print("\nheader_breaks: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
