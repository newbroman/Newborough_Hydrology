#!/usr/bin/env python3
"""
refresh_mirrors.py
==================
Regenerate the markdown mirrors that the document lints read.

The ODTs (and the report's master .odm) are the editing surface; the mirrors
under report_edits/text/ and docs/**/ are the machine-readable surface that tools/audit_number_drift.py and
tools/cite_check.py search. A mirror that is not regenerated after an ODT edit
silently turns every lint into a check of yesterday's text — which is exactly
how five stale cluster coefficients survived in report9 and Paper 1 while the
tooling reported clean.

Mirrors are GENERATED. Never hand-edit one; the next run overwrites it.

Versioned documents (Methods Supplement, Supplementary Material, Papers) mirror
their HIGHEST version only, resolved by natural sort of the _v1_9_10-style
suffix, so a bumped filename is picked up without editing this script.

Usage:
    python3 tools/refresh_mirrors.py            # refresh everything
    python3 tools/refresh_mirrors.py --check    # fail if any mirror is stale
    python3 tools/refresh_mirrors.py --only report10
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) - 2026-08-20. report.odm, the
#        LibreOffice MASTER document, joins the mirror set. The master is not
#        an empty shell of links: it carries the title block and the whole
#        ABSTRACT, text that exists in no chapter file. The source glob was
#        "report*.odt", which cannot match a ".odm", so every number in the
#        abstract - five LCSC values, two beta_2 values, the NSE improvement,
#        the clearfell and scraping steps - sat outside the corpus that
#        cite_check.py and audit_number_drift.py search, and had never once
#        been checked against the pipeline. The mirror lands at
#        report_edits/text/report.md, which cite_check's existing
#        "report_edits/text/report*.md" glob already sweeps, so nothing in
#        cite_check.py changes: the corpus follows the mirror, as designed.
#
# 1.0.0  marks the module's state before this change; it carried no
#        __version__ constant previously.

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# (source glob, mirror directory, versioned?) — versioned sources mirror the
# highest version only and drop the version from the mirror name, so the mirror
# path is stable across bumps.
SOURCES = [
    ("report_edits/odt/report*.odt", "report_edits/text", False),
    # The master document, mirrored as its own source. Everything the report
    # says before Chapter 6 - title block, author block and the abstract -
    # lives in report.odm and nowhere else, so mirroring only the chapters
    # left the abstract unchecked. pandoc reads the master's own content.xml;
    # the linked sub-documents are mirrored by the line above, so no chapter
    # text is duplicated in the corpus. Not versioned: the filename is stable.
    ("report_edits/odt/report.odm", "report_edits/text", False),
    ("docs/report/Newborough_Methods_Supplement_v*.odt", "docs/report/text", True),
    ("docs/report/Supplementary_Material_v*.odt", "docs/report/text", True),
    ("docs/papers/paper_1/Paper1_v*.odt", "docs/papers/paper_1/text", True),
    ("docs/papers/paper_1/PAPER1_SI_methods_v*.odt", "docs/papers/paper_1/text", True),
    # Paper 2's files are named Hollingham_2026_Paper2_amended[_v2].odt, so the
    # old "Paper2_v*.odt" pattern never matched anything and the paper was
    # silently outside the corpus - present in this list, absent from the net.
    ("docs/papers/paper_2/Hollingham_2026_Paper2_amended*.odt",
     "docs/papers/paper_2/text", True),
    # Reader-facing documents. They quote the same pipeline numbers as the
    # report, and until 2026-08-18 nothing would have told us when one drifted.
    ("docs/academic_summaries/academic_Summary_v*.odt",
     "docs/academic_summaries/text", True),
    ("docs/academic_summaries/crynodeb_academaidd_v*.odt",
     "docs/academic_summaries/text", True),
    ("docs/public_summaries/public_summary_*.odt",
     "docs/public_summaries/text", False),
    ("docs/web_tools/NRG_Web_Tools_*.odt", "docs/web_tools/text", False),
]

_VER = re.compile(r"_v(\d+(?:[_.]\d+)*)\.odt$")



# THE MIRRORS ARE NOT PANDOC-VERSION-INDEPENDENT, AND OLD PANDOC LOSES CONTENT.
#
# This project runs on two machines — the bridge VM and the cloud container —
# and their pandoc differs. Regenerating report8 on the bridge's 2.9.2.1 against
# the committed mirror produced 2,300 changed lines, of which:
#
#   cosmetic   setext headings instead of ATX (pandoc changed the default at
#              2.11.2), and underscores escaped where the committed mirrors
#              leave them bare — run\_analysis.py against run_analysis.py.
#   NOT cosmetic
#              DISPLAY EQUATIONS DROPPED ENTIRELY. report8's Thornthwaite heat
#              index, $$I = \sum (T_m/5)^{1.514}$$, is simply absent from the
#              2.9.2.1 output.
#
# The mirrors are the surface cite_check and symbol_check search. A mirror that
# has quietly lost its equations is worse than a stale one, because nothing
# reports it: the lints go on passing over text that is no longer there.
#
# Verified 2026-08-23: pandoc 3.1.3 reproduces ALL 23 committed mirrors byte for
# byte — not one sampled document. `--verify` is that check, and re-running it is
# how the claim stays true rather than becoming a comment nobody tests.
#
# So the generator is pinned, not merely configured. Writing on an unsupported
# pandoc ABORTS. --check WARNS and does not gate, because a "drift" report that
# is really a version difference would train the reader to ignore the gate.
MIN_PANDOC = (3, 0)


def _pandoc_version() -> tuple:
    import subprocess
    out = subprocess.run(["pandoc", "--version"], capture_output=True, text=True).stdout
    m = re.search(r"pandoc\s+(\d+)\.(\d+)(?:\.(\d+))?", out)
    if not m:
        raise SystemExit("cannot determine the pandoc version")
    return tuple(int(g) for g in m.groups(default="0"))


PANDOC_VERSION = _pandoc_version()
PANDOC_OK = PANDOC_VERSION >= MIN_PANDOC


def require_supported_pandoc(writing: bool) -> None:
    if PANDOC_OK:
        return
    v = ".".join(str(n) for n in PANDOC_VERSION)
    msg = (f"pandoc {v} is below the pinned minimum "
           f"{'.'.join(str(n) for n in MIN_PANDOC)}. It drops display equations "
           f"from the mirrors and escapes underscores the committed mirrors "
           f"leave bare.")
    if writing:
        raise SystemExit(
            f"  ABORT  {msg}\n"
            f"         Regenerate on a machine with pandoc >= "
            f"{'.'.join(str(n) for n in MIN_PANDOC)} (the cloud container has "
            f"3.1.3); do not commit mirrors written here.")
    print(f"  WARN   {msg}")
    print("         --check compares MODIFICATION TIMES ONLY — it never reads the "
          "content — so")
    print("         a mirror written here will read as current while missing its "
          "equations.")


_ATX_FLAG = "--markdown-headings=atx"

def _version_key(p: Path):
    m = _VER.search(p.name)
    return [int(n) for n in re.split(r"[_.]", m.group(1))] if m else [-1]


def _stem_without_version(p: Path) -> str:
    return _VER.sub("", p.name) or p.stem


def resolve() -> list[tuple[Path, Path]]:
    """Return [(source_odt, mirror_md)] after version resolution."""
    jobs: list[tuple[Path, Path]] = []
    for pattern, mirror_dir, versioned in SOURCES:
        matches = sorted(REPO.glob(pattern))
        if not matches:
            continue
        if versioned:
            latest = max(matches, key=_version_key)
            matches = [latest]
        for src in matches:
            name = _stem_without_version(src) if versioned else src.stem
            jobs.append((src, REPO / mirror_dir / f"{name}.md"))
    return jobs


def convert(src: Path, dst: Path) -> None:
    require_supported_pandoc(writing=True)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["pandoc", "-f", "odt", "-t", "markdown", "--wrap=none",
             _ATX_FLAG,
             "-o", str(Path(tmp) / "out.md"), str(src)],
            check=True, capture_output=True,
        )
        text = (Path(tmp) / "out.md").read_text(encoding="utf8")
    banner = (f"<!-- GENERATED MIRROR of {src.relative_to(REPO)} — do not edit.\n"
              f"     Regenerate with: python3 tools/refresh_mirrors.py -->\n\n")
    dst.write_text(banner + text, encoding="utf8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report stale mirrors and exit non-zero; write nothing")
    ap.add_argument("--only", default=None, help="substring filter on source name")
    # Ask for the resolved source rather than guessing it. `ls | tail` sorts
    # v1_9 AFTER v1_18, which on 2026-08-23 produced a confident report that
    # Paper 1's Table 9 was stale on four axes — read out of Paper1_v1_9.odt
    # while the live document was Paper1_v1_19.odt and the table was correct.
    # resolve() has always known which file is current; nothing exposed it.
    ap.add_argument("--paths", action="store_true",
                    help="print the resolved source -> mirror pairs and exit")
    # --check reads modification times and nothing else, and says so. That is
    # cheap and it is also how two people can spend an evening arguing about
    # pandoc: on 2026-08-23 a mirror was compared against a regeneration of a
    # source that had been re-saved by LibreOffice in between, the difference
    # was attributed to a version divergence between two pandocs, and the
    # claim survived because nothing could answer "is this mirror actually
    # what its source produces?". --verify answers exactly that, by
    # regenerating into a temporary directory and comparing bytes.
    ap.add_argument("--verify", action="store_true",
                    help="regenerate each mirror in a temp dir and byte-compare; "
                         "reads content, not timestamps")
    args = ap.parse_args()

    jobs = resolve()
    if args.only:
        jobs = [j for j in jobs if args.only in j[0].name]
    if not jobs:
        print("No sources matched.")
        return 1

    if args.paths:
        for src, dst in jobs:
            print(f"{src.relative_to(REPO)}  ->  {dst.relative_to(REPO)}")
        return 0
    if args.check:
        require_supported_pandoc(writing=False)

    if args.verify:
        require_supported_pandoc(writing=True)
        drift = []
        for src, dst in jobs:
            if not dst.exists():
                print(f"MISSING  {dst.relative_to(REPO)}")
                drift.append(dst)
                continue
            with tempfile.TemporaryDirectory() as tmp:
                probe = Path(tmp) / "probe.md"
                convert(src, probe)
                same = probe.read_bytes() == dst.read_bytes()
            print(f"{'MATCH' if same else 'DRIFT'}    {dst.relative_to(REPO)}"
                  f"   <- {src.relative_to(REPO)}")
            if not same:
                drift.append(dst)
        v = ".".join(str(n) for n in PANDOC_VERSION)
        if drift:
            print(f"\n{len(drift)} mirror(s) are NOT what their source produces "
                  f"under pandoc {v}.\nEither the source changed since the mirror "
                  f"was written, or this pandoc differs from the one that wrote "
                  f"it.\nRegenerate, and if the content then changes, the mirror "
                  f"was stale; if it does not, the two pandocs agree after all.")
            return 1
        print(f"\nAll {len(jobs)} mirrors reproduce byte for byte under "
              f"pandoc {v}.")
        return 0

    stale = []
    for src, dst in jobs:
        fresh = dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime
        if args.check:
            print(f"{'OK   ' if fresh else 'STALE'}  {dst.relative_to(REPO)}"
                  f"   <- {src.relative_to(REPO)}")
            if not fresh:
                stale.append(dst)
            continue
        convert(src, dst)
        print(f"  wrote {dst.relative_to(REPO)}  <- {src.relative_to(REPO)}")

    if args.check and stale:
        print(f"\n{len(stale)} mirror(s) stale — run tools/refresh_mirrors.py")
        return 1
    if args.check:
        print("\nAll mirrors current.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
