#!/usr/bin/env python3
"""
exhibit_keep.py — keep an exhibit on one page, and with its caption.

WHAT IT SETS

  tables   fo:keep-with-next="always" on the table's style, because in this
           corpus the caption FOLLOWS the table; and
           style:may-break-between-rows="false" when the table is short enough
           to fit a page. A table longer than MAX_ROWS is left splittable: a
           table that cannot break and cannot fit is pushed whole to the next
           page and then overflows it, which is worse than a clean split.

  figures  fo:keep-with-next="always" on a paragraph that holds ONLY a frame
           AND is immediately followed by a caption. Both conditions matter.
           report9 writes most figures with the image and the caption in one
           paragraph, where nothing is needed; the plain-layout figures put them
           in two. Of the 13 frame-only paragraphs in report9, most are followed
           by body text or a table, and binding those to the next paragraph
           would drag unrelated prose onto the figure's page.

  A paragraph's style is shared, so the property cannot be set on it directly —
  "Cap" is used by captions that must NOT keep with what follows them. Each
  qualifying paragraph is repointed to a derived automatic style
  NRGKeep_<base>, parent <base>, carrying only the keep.

Usage:
    python3 tools/exhibit_keep.py --check
    python3 tools/exhibit_keep.py --apply [--doc report9]
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-20.

import argparse
import pathlib
import re
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import odt_edit                                            # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
MAX_ROWS = 25
TAG = re.compile(r"<[^>]+>")
FRAME_ONLY = re.compile(r"<text:p([^>]*)>\s*(<draw:frame.*?</draw:frame>)\s*</text:p>", re.S)


def table_subs(xml: str):
    """(old, new, 1) for each table style that needs a keep property."""
    out, seen = [], set()
    for m in re.finditer(r'<table:table table:name="([^"]+)" table:style-name="([^"]+)"', xml):
        name, style = m.group(1), m.group(2)
        if style in seen:
            continue
        seen.add(style)
        end = xml.find("</table:table>", m.end())
        nrows = len(re.findall(r"<table:table-row", xml[m.start():end]))
        sm = re.search(rf'<style:style style:name="{re.escape(style)}" '
                       rf'style:family="table">\s*<style:table-properties([^>]*)/>', xml)
        if not sm:
            continue
        attrs, add = sm.group(1), ""
        if "fo:keep-with-next" not in attrs:
            add += ' fo:keep-with-next="always"'
        if nrows <= MAX_ROWS and "may-break-between-rows" not in attrs:
            add += ' style:may-break-between-rows="false"'
        if add:
            out.append((sm.group(0), sm.group(0)[:-2] + add + "/>", 1))
    return out


def figure_subs(xml: str):
    """(old, new, 1) for frame-only paragraphs that a caption follows."""
    out, bases = [], set()
    for m in FRAME_ONLY.finditer(xml):
        after = TAG.sub("", xml[m.end():m.end() + 400]).strip()
        if not re.match(r"(Figure|Table)\b", after):
            continue
        s = re.search(r'text:style-name="([^"]+)"', m.group(1))
        if not s or s.group(1).startswith("NRGKeep_"):
            continue
        base = s.group(1)
        bases.add(base)
        new = m.group(0).replace(f'text:style-name="{base}"',
                                 f'text:style-name="NRGKeep_{base}"', 1)
        out.append((m.group(0), new, 1))
    return out, bases


def style_decls(xml: str, bases: set[str]):
    decls = "".join(
        f'<style:style style:name="NRGKeep_{b}" style:family="paragraph" '
        f'style:parent-style-name="{b}">'
        f'<style:paragraph-properties fo:keep-with-next="always"/></style:style>'
        for b in sorted(bases) if f'style:name="NRGKeep_{b}"' not in xml)
    if not decls:
        return []
    return [("</office:automatic-styles>", decls + "</office:automatic-styles>", 1)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--doc", default=None)
    args = ap.parse_args()
    if not (args.apply or args.check):
        ap.error("choose --check or --apply")

    odts = sorted((REPO / "report_edits/odt").glob("report*.odt"))
    if args.doc:
        odts = [p for p in odts if p.stem == args.doc]
    rc = 0
    for path in odts:
        xml = zipfile.ZipFile(path).read("content.xml").decode("utf-8")
        t = table_subs(xml)
        f, bases = figure_subs(xml)
        subs = style_decls(xml, bases) + t + f
        if not subs:
            print(f"  ok      {path.name}: exhibits already keep with their captions")
            continue
        rc = 1 if args.check else rc
        print(f"  {'would fix' if args.check else 'fixing  '} {path.name}: "
              f"{len(t)} table style(s), {len(f)} figure paragraph(s)")
        if args.apply and not odt_edit.edit(path, path, subs, expect=len(subs),
                                            allow_tag_change=True):
            rc = 1
    print("\nexhibit_keep: " + ("exhibits can be split from their captions — run --apply"
                                if (args.check and rc) else "OK"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
