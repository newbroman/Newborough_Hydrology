#!/usr/bin/env python3
"""
symbol_apply — apply one registered symbol rename across the ODTs.

symbol_check finds and classifies; this applies. They share the register and the
classification code, so what gets renamed is exactly what the audit said would be.

The hard part is not the rename. It is that a glyph carries several senses and
only one of them moves: the same letter D must become z₀ where it is the drainage
datum and stay D where it is the hydraulic diffusivity, sometimes in the same
chapter. A find-and-replace cannot do that; nor can anything that works on the
markdown mirrors, because the mirrors are generated and the ODT is the editing
surface.

So the method is:

  1. Flatten content.xml to plain text, KEEPING a map from each flat character
     back to its position in the XML. Only the gaps between tags are text, so a
     rename can never touch a style name, an attribute or a bookmark id.
  2. Run symbol_check's own occurrence guard and sense classifier over that flat
     text — the same regex, the same register, the same context windows.
  3. Keep only occurrences classified as the requested sense, and only where the
     register marks that sense displaced.
  4. Hand the character ranges to odt_edit.edit_spans(), which applies them under
     the full set of structural guards.

Dry run by default. --apply writes, and always to a bumped filename supplied by
the caller: this tool never edits a versioned document in place.

Usage
    python3 tools/symbol_apply.py --sense D_datum                    # dry run
    python3 tools/symbol_apply.py --sense D_datum --apply
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-22. First issue, built for
#   the D -> z₀ datum rename (M21). The audit had produced a 129-edit proposal
#   with nothing able to apply it except by hand, across seven documents, on a
#   glyph that means three different things.

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import symbol_check as sc          # noqa: E402  — occurrence guard + classifier
from odt_edit import edit_spans    # noqa: E402
from doc_paths import ODT_GLOB, ODM_GLOB

REPO = Path(__file__).resolve().parents[1]

# Which ODT each mirror in symbol_check.DOC_GLOBS came from. Versioned documents
# name the CURRENT version and the bumped target; unversioned ones are edited in
# place, as the report chapters are.
TARGETS = [
    # (glob for the source ODT, versioned?)
    (ODT_GLOB, False),
    (ODM_GLOB, False),
    ("docs/report/Newborough_Methods_Supplement_v*.odt", True),
    ("docs/report/Supplementary_Material_v*.odt", True),
    ("docs/papers/paper_1/Paper1_v*.odt", True),
    ("docs/papers/paper_1/PAPER1_SI_methods_v*.odt", True),
    ("docs/papers/paper_2/Hollingham_2026_Paper2_amended*.odt", True),
    ("docs/academic_summaries/academic_Summary_v*.odt", True),
    ("docs/academic_summaries/crynodeb_academaidd_v*.odt", True),
]

_VER = re.compile(r"_v(\d+(?:_\d+)*)\.odt$")


def _version_key(p: Path):
    m = _VER.search(p.name)
    return [int(x) for x in m.group(1).split("_")] if m else [-1]


def newest(glob: str, versioned: bool) -> list[Path]:
    paths = sorted(REPO.glob(glob))
    if not paths:
        return []
    if not versioned:
        return paths
    return [max(paths, key=_version_key)]


def bumped_name(p: Path) -> Path:
    """Doc_v1_9_38.odt -> Doc_v1_9_39.odt; unversioned names are returned as-is."""
    m = _VER.search(p.name)
    if not m:
        return p
    parts = m.group(1).split("_")
    parts[-1] = str(int(parts[-1]) + 1)
    return p.with_name(p.name[:m.start()] + "_v" + "_".join(parts) + ".odt")


def flatten_with_map(xml: str):
    """(flat text, [(flat_start, xml_start, length)]) over the text segments.

    Only the gaps between tags become flat text, so nothing this returns can
    point inside markup.
    """
    flat, spans, pos = [], [], 0
    out_len = 0
    for m in re.finditer(r"<[^>]+>", xml):
        seg = xml[pos:m.start()]
        if seg:
            flat.append(seg)
            spans.append((out_len, pos, len(seg)))
            out_len += len(seg)
        pos = m.end()
    tail = xml[pos:]
    if tail:
        flat.append(tail)
        spans.append((out_len, pos, len(tail)))
    return "".join(flat), spans


def flat_to_xml(spans, flat_i: int) -> int | None:
    for f0, x0, n in spans:
        if f0 <= flat_i < f0 + n:
            return x0 + (flat_i - f0)
    return None


def plan_for(path: Path, senses: list[dict], sense_id: str, glyph: str):
    """[(xml_start, xml_end, replacement)] for one document."""
    import zipfile
    xml = zipfile.ZipFile(path).read("content.xml").decode("utf-8")
    flat, spans = flatten_with_map(xml)
    target = next(s for s in senses if s["sense_id"] == sense_id)
    out = []
    for f_start, f_end in sc.occurrences(flat, glyph):
        hits = sc.classify(flat, (f_start, f_end), senses)
        if hits != [sense_id]:
            continue
        x0 = flat_to_xml(spans, f_start)
        x1 = flat_to_xml(spans, f_end - 1)
        if x0 is None or x1 is None or (x1 + 1 - x0) != (f_end - f_start):
            continue                      # occurrence straddles markup — skip it
        out.append((x0, x1 + 1, target["replacement"],
                    re.sub(r"\s+", " ", flat[max(0, f_start - 60):f_end + 60])))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sense", required=True, help="sense_id from the register")
    ap.add_argument("--apply", action="store_true", help="write the bumped ODTs")
    ap.add_argument("--context", type=int, default=3,
                    help="how many contexts to print per document")
    args = ap.parse_args()

    reg = sc.load_register()
    row = next((r for r in reg if r["sense_id"] == args.sense), None)
    if row is None:
        sys.exit(f"no sense {args.sense!r} in {sc.REGISTER}")
    if row["status"] != "displaced" or not row["replacement"]:
        sys.exit(f"{args.sense} is {row['status']!r} with replacement "
                 f"{row['replacement']!r} — nothing to apply")
    glyph = row["glyph"]
    senses = [r for r in reg if r["glyph"] == glyph and r.get("form", "bare") == "bare"]

    print("=" * 78)
    print(f"SYMBOL APPLY — {glyph} / {args.sense} -> {row['replacement']}")
    print(f"  {row['meaning']}")
    print("=" * 78)
    if not args.apply:
        print("  DRY RUN — nothing is written. Add --apply.\n")

    total, failures = 0, 0
    for glob, versioned in TARGETS:
        for p in newest(glob, versioned):
            plan = plan_for(p, senses, args.sense, glyph)
            if not plan:
                continue
            total += len(plan)
            dst = bumped_name(p) if versioned else p
            print(f"\n  {p.relative_to(REPO)}  ->  {dst.name}   {len(plan)} occurrence(s)")
            for _, _, _, ctx in plan[:args.context]:
                print(f"      ...{ctx}...")
            if len(plan) > args.context:
                print(f"      ... {len(plan) - args.context} more")
            if args.apply:
                spans = [(a, b, r) for a, b, r, _ in plan]
                if not edit_spans(p, dst, spans, len(spans)):
                    failures += 1

    print("\n" + "=" * 78)
    print(f"  {total} occurrence(s) of {glyph} as {args.sense}"
          + ("" if args.apply else "  — dry run, nothing written"))
    if failures:
        print(f"  {failures} document(s) FAILED their guards and were not written")
    if args.apply and not failures:
        print("  Refresh mirrors, then re-run symbol_check to confirm the sense is clear.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
