#!/usr/bin/env python3
"""
odt_text.py — plain text straight out of an ODT, with no pandoc in the way.

WHY
    Every document lint in this project reads a markdown mirror produced by
    pandoc. That surface has cost real accuracy twice in one day:

      * the mirrors are pandoc-VERSION dependent. Regenerated on the bridge VM's
        2.9.2.1 they lose display equations outright — report8's Thornthwaite
        heat index simply vanishes — and escape underscores the committed
        mirrors leave bare.
      * they can be STALE, and refresh_mirrors --check only compares
        modification times, so a mirror that is newer and wrong reads as current.

    Neither failure is visible to the lints that depend on them. Reading the ODT
    directly removes the whole class: there is no second artefact to drift, no
    external binary, and no version to pin.

THE ONE THING THAT MUST BE RIGHT
    LibreOffice splits runs mid-token. report12 held the number −1.16 as

        −1.1<text:span text:style-name="T9">6</text:span>

    so a tag-stripper that substitutes a SPACE for markup — which is what
    symbol_check does to the mirrors — would read "−1.1" and "6" as two tokens
    and miss the citation. Tags are therefore removed with NOTHING between, and
    paragraphs are the only unit that introduces a break. This is also why the
    extraction is done per-paragraph rather than over the whole file.

WHAT IT IS NOT
    Not a replacement for the mirrors as a TRACKED artefact. The ODTs are
    gitignored, so the mirrors are the only representation of document content
    that git can diff, and they stay for that reason. What changes is which
    surface the LINTS trust.

USAGE
    from odt_text import extract
    text = extract("report_edits/odt/report9.odt")

    python3 tools/odt_text.py --compare        # every ODT against its mirror
    python3 tools/odt_text.py --compare --numbers-only
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-23

import argparse
import pathlib
import re
import sys
import zipfile
from xml.sax.saxutils import unescape

REPO = pathlib.Path(__file__).resolve().parent.parent

# A paragraph or a heading. Both carry running text; nothing else does.
_PARA = re.compile(r"<text:(p|h)\b[^>]*>(.*?)</text:\1>", re.S)
_TAG = re.compile(r"<[^>]+>")
_ENTITIES = {"&apos;": "'", "&quot;": '"'}

# Tags that stand for whitespace rather than for nothing.
_SPACE_TAGS = [
    (re.compile(r"<text:s\s*/>"), " "),
    (re.compile(r'<text:s\s+text:c="(\d+)"\s*/>'), None),   # repeated spaces
    (re.compile(r"<text:tab\s*/>"), "\t"),
    (re.compile(r"<text:line-break\s*/>"), "\n"),
]


def _paragraph_text(inner: str) -> str:
    def _spaces(m):
        return " " * int(m.group(1))
    inner = re.sub(r'<text:s\s+text:c="(\d+)"\s*/>', _spaces, inner)
    for pat, rep in _SPACE_TAGS:
        if rep is not None:
            inner = pat.sub(rep, inner)
    # Every remaining tag goes with NO separator, so a run split mid-token
    # rejoins. This is the whole point of the module.
    inner = _TAG.sub("", inner)
    for ent, ch in _ENTITIES.items():
        inner = inner.replace(ent, ch)
    return unescape(inner)


# An ODF formula is NOT text in content.xml. It is an embedded part,
# "Object N/content.xml", holding a MathML tree and a StarMath annotation of the
# same expression, referenced from the flow by a placeholder:
#
#     <draw:object xlink:href="./Object 1" .../>
#
# report8 carries 82 of them, and everything inside — the Thornthwaite exponent
# 1.514, the heat-index constants — is invisible to a reader of content.xml
# alone. This is the same structure the D-055 datum rename had to edit twice,
# once as MathML and once as StarMath. The StarMath annotation is the readable
# form, so it is spliced in at the placeholder and travels with its paragraph.
_OBJREF = re.compile(r'<draw:object[^>]*xlink:href="\./([^"]+)"[^>]*/?>')
_ANNOT = re.compile(r"<annotation[^>]*>(.*?)</annotation>", re.S)


def _formulas(z: zipfile.ZipFile) -> dict:
    out = {}
    for name in z.namelist():
        if not name.endswith("/content.xml") or not name.startswith("Object"):
            continue
        m = _ANNOT.search(z.read(name).decode("utf-8", "replace"))
        if m:
            out[name.rsplit("/", 1)[0]] = unescape(m.group(1)).strip()
    return out


def extract(path, formulas: bool = True) -> str:
    """All running text of an ODT/ODM, one paragraph per line, in document order.

    Embedded formulas are spliced in as StarMath unless formulas=False.
    """
    z = zipfile.ZipFile(path)
    xml = z.read("content.xml").decode("utf-8")
    if formulas:
        eqs = _formulas(z)
        xml = _OBJREF.sub(lambda m: " " + eqs.get(m.group(1), "") + " ", xml)
    return "\n".join(_paragraph_text(m.group(2)) for m in _PARA.finditer(xml))


# --- validation --------------------------------------------------------------

_NUM = re.compile(r"-?\d+(?:\.\d+)?")

# Noise that exists ONLY in a pandoc mirror and is not document content.
# Without these the comparison reports hundreds of false losses:
#   []{#anchor-100}                     pandoc-generated anchor ids
#   Pictures/10000000000007...png       image filenames
#   {width="15.803cm" height="9.5cm"}   image geometry
#   0.10--0.18                          en-dash ranges, which tokenise as a
#                                       negative number in the mirror and as two
#                                       positives in the ODT
_MIRROR_NOISE = [
    re.compile(r"\[\]\{#[^}]*\}"),
    re.compile(r"Pictures/[^)\s]+"),
    re.compile(r'\{width="[^"]*"\s*height="[^"]*"\}'),
    re.compile(r"\{width=\"[^\"]*\"\}"),
]


def _normalise(text: str, is_mirror: bool) -> str:
    if is_mirror:
        for pat in _MIRROR_NOISE:
            text = pat.sub(" ", text)
        text = text.replace("--", " ")          # pandoc en-dash
    text = text.replace("−", "-").replace("–", " ").replace("—", " ")
    return text.replace(",", "")


def _numbers(text: str, is_mirror: bool = False) -> set:
    return set(_NUM.findall(_normalise(text, is_mirror)))


def compare(numbers_only: bool) -> int:
    sys.path.insert(0, str(REPO / "tools"))
    import refresh_mirrors as rm

    rc = 0
    print("=" * 78)
    print("ODT extraction against the pandoc mirrors")
    print("=" * 78)
    for src, dst in rm.resolve():
        if not dst.exists():
            continue
        odt = extract(src)
        mirror = dst.read_text(encoding="utf8")
        a, b = _numbers(odt), _numbers(mirror, is_mirror=True)
        only_mirror = b - a
        only_odt = a - b
        flag = "  " if not only_mirror else "!!"
        print(f"{flag} {dst.name:44s} odt {len(a):5d}  mirror {len(b):5d}  "
              f"mirror-only {len(only_mirror):4d}  odt-only {len(only_odt):4d}")
        if only_mirror:
            rc = 1
            print(f"       in the mirror, MISSING from the ODT extraction: "
                  f"{sorted(only_mirror)[:12]}")
        if only_odt and not numbers_only:
            print(f"       in the ODT, absent from the mirror: "
                  f"{sorted(only_odt)[:12]}")
    print()
    print("  mirror-only numbers are the failure that matters: they would mean the"
          "\n  extraction loses something the lints currently see.")
    return rc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--numbers-only", action="store_true")
    ap.add_argument("path", nargs="?")
    a = ap.parse_args()
    if a.compare:
        return compare(a.numbers_only)
    if not a.path:
        ap.error("give a path, or --compare")
    print(extract(a.path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
