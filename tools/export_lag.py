#!/usr/bin/env python3
"""
export_lag.py — which published PDFs are older than the documents they came from.

WHY
    A PDF is a derived artefact with no link back to its source, so it goes stale
    silently. That is not only untidy — `report_edits/figref_lint.py` PARSES the
    exported PDF, because it is the only artefact where captions and in-text
    references both carry resolved numbers. On 2026-08-23 report.pdf was dated
    06:51 while four of its source documents had been edited after it, so the
    figure lint was checking a document that no longer existed and reporting it
    clean. A check that reads a stale artefact does not fail; it lies.

    The same shape as the pandoc guard in refresh_mirrors, and the same remedy:
    make the staleness visible, and make the tool that depends on it refuse.

WHERE THE MAPPING COMES FROM
    tools/build_pdfs.sh already carries source-glob -> PDF for every document it
    builds. That array is parsed here rather than copied, so the two cannot drift.

    report.pdf is the exception build_pdfs.sh names itself: report.odm is a master
    document and is exported by hand. Its sources are the master AND all ten
    linked sub-documents, since editing any chapter changes the assembled PDF.
    That is the pairing this project actually gets wrong, so it is stated
    explicitly below.

EXIT
    0   always, by default — this is advisory. A PDF export is slow and manual,
        and a gate that fires between every ODT edit and the next export would be
        switched off inside a week, which is the reasoning check_all already
        applies to pipeline_lint's literal check.
    --strict makes it gate, for use before a release.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-23

import argparse
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
BUILD_PDFS = REPO / "tools/build_pdfs.sh"

# The hand-exported master, which build_pdfs.sh deliberately does not build.
MASTER = ("docs/report/report.pdf",
          ["report_edits/odt/report.odm", "report_edits/odt/report*.odt"])

_PAIR = re.compile(r'^\s*"([^"|]+)\|([^"|]+)"\s*$')


def pairs() -> list[tuple[str, list[str]]]:
    """[(pdf, [source globs])] — build_pdfs.sh's array, plus the master."""
    out: list[tuple[str, list[str]]] = []
    if BUILD_PDFS.exists():
        for line in BUILD_PDFS.read_text(encoding="utf8").splitlines():
            m = _PAIR.match(line)
            if m:
                out.append((m.group(2), [m.group(1)]))
    out.append(MASTER)
    return out


_VER = re.compile(r"_v(\d+(?:[._]\d+)*)")


def _version_key(p: pathlib.Path):
    m = _VER.search(p.name)
    return [int(n) for n in re.split(r"[._]", m.group(1))] if m else [-1]


def _newest(globs: list[str]) -> list[pathlib.Path]:
    """The sources that actually matter for a PDF.

    A VERSIONED glob (one containing "_v") names a family whose live member is
    the highest version — comparing a PDF against v2..v10 individually says
    nothing, since the older ones are history. An unversioned glob names every
    file it matches, which is what the hand-exported master needs: report.pdf
    depends on the master AND all ten linked sub-documents, because editing any
    chapter changes the assembled export.
    """
    found: list[pathlib.Path] = []
    for g in globs:
        matches = sorted(REPO.glob(g))
        if not matches:
            continue
        found += [max(matches, key=_version_key)] if "_v" in g else matches
    return found


def run(strict: bool) -> int:
    print("=" * 78)
    print("EXPORT LAG — is each published PDF newer than its sources?")
    print("=" * 78)
    lagging = 0
    for pdf_rel, globs in pairs():
        pdf = REPO / pdf_rel
        srcs = _newest(globs)
        if not srcs:
            continue
        if not pdf.exists():
            print(f"\n  MISSING  {pdf_rel} has never been built")
            lagging += 1
            continue
        pt = pdf.stat().st_mtime
        ahead = [s for s in srcs if s.stat().st_mtime > pt]
        if ahead:
            lagging += 1
            print(f"\n  STALE    {pdf_rel}")
            print(f"           {len(ahead)} source(s) edited since it was built:")
            for s in sorted(ahead, key=lambda x: -x.stat().st_mtime):
                print(f"             {s.relative_to(REPO)}")
    # A PDF with no mapping is never checked by anything, which is the same
    # false assurance this tool exists to remove. Paper 2's published PDF sat two
    # months and eight versions behind its ODT precisely because build_pdfs.sh
    # had no pairing for it, so nothing — including the first version of this
    # check — ever looked.
    mapped = {(REPO / pdf).resolve() for pdf, _ in pairs()}
    unmapped = sorted(
        q for q in REPO.glob("docs/**/*.pdf")
        if q.resolve() not in mapped
        and not any(part.startswith("_") for part in q.relative_to(REPO).parts)
    )
    if unmapped:
        print(f"\n  UNMAPPED — {len(unmapped)} published PDF(s) with no source "
              f"pairing in tools/build_pdfs.sh.")
        print("           Nothing rebuilds or checks these. Either add a pairing "
              "or confirm the")
        print("           PDF is authored directly and has no ODT source.")
        for q in unmapped:
            print(f"             {q.relative_to(REPO)}")

    print()
    if lagging:
        print(f"  {lagging} published PDF(s) behind their sources.")
        print("  Rebuild the buildable ones with tools/build_pdfs.sh; report.pdf is")
        print("  exported by hand from report.odm (File > Export as PDF).")
        print("  Until then report_edits/figref_lint.py is reading a document that")
        print("  no longer exists and will report it clean.")
    else:
        print("  every published PDF is at least as new as its sources.")
    return 1 if (lagging and strict) else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero when anything lags (for a release check)")
    return run(ap.parse_args().strict)


if __name__ == "__main__":
    sys.exit(main())
