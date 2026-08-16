#!/usr/bin/env python3
"""
refresh_mirrors.py
==================
Regenerate the markdown mirrors that the document lints read.

The ODTs are the editing surface; the mirrors under report_edits/text/ and
docs/**/ are the machine-readable surface that tools/audit_number_drift.py and
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
    ("docs/report/Newborough_Methods_Supplement_v*.odt", "docs/report/text", True),
    ("docs/report/Supplementary_Material_v*.odt", "docs/report/text", True),
    ("docs/papers/paper_1/Paper1_v*.odt", "docs/papers/paper_1/text", True),
    ("docs/papers/paper_1/PAPER1_SI_methods_v*.odt", "docs/papers/paper_1/text", True),
    ("docs/papers/paper_2/Paper2_v*.odt", "docs/papers/paper_2/text", True),
]

_VER = re.compile(r"_v(\d+(?:[_.]\d+)*)\.odt$")


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
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["pandoc", "-f", "odt", "-t", "markdown", "--wrap=none",
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
    args = ap.parse_args()

    jobs = resolve()
    if args.only:
        jobs = [j for j in jobs if args.only in j[0].name]
    if not jobs:
        print("No sources matched.")
        return 1

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
