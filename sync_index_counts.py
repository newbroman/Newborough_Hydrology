#!/usr/bin/env python3
"""
====================================================================================
sync_index_counts.py — stamp index.html's pipeline counts from the manifest
====================================================================================

Purpose:
    index.html is hand-maintained and is the only project document that states
    the pipeline step counts without quoting outputs/pipeline_manifest.json.
    On 2026-08-07 it was found carrying "46 analytical steps across 17 phases,
    plus a single post-processing phase" — an eighteenth phase that does not
    exist, Phase 17 being the post-processing phase and already inside the 17.

    This script keeps the numbers in step with the manifest, which is the
    canonical artefact per the project rule that step counts are derived and
    never hard-typed.

How it works:
    Numbers in index.html are wrapped in HTML comment markers, invisible when
    rendered:

        <!--PL:total-->49<!--/PL:total-->

    The script reads the manifest and rewrites whatever sits between each
    marker pair. The numbers stay in the HTML source, so the page is correct
    when viewed locally or with JavaScript disabled.

    Recognised keys:

        PL:total        total_registered           registered orchestrator steps
        PL:analytical   analytical_headline        sub-runner-EXPANDED count
        PL:phases       analytical_phases
        PL:display      by_tier.display_utility

    NOTE on total vs analytical. These are on different bases and are NOT
    additive: total counts run_09/run_10 as one entry each, while analytical
    expands them into their constituent modules. "46 analytical + 4
    display/utility" against a total of 49 is therefore not an arithmetic
    error. See run_analysis.py lines 427-441.

What it does NOT do:
    Only the numbers are managed. If a phase were renamed or the tier
    structure changed, the counts would update while the surrounding prose
    went stale. The marker names are the only signal to a future editor that
    these numbers are generated.

Usage:
    python3 tools/sync_index_counts.py                 # stamp index.html
    python3 tools/sync_index_counts.py --check         # report only, exit 1 if stale
    python3 tools/sync_index_counts.py --index PATH --manifest PATH

Exit codes:
    0  success (or --check and already current)
    1  --check found stale values
    2  a real failure: missing file, unreadable manifest, missing key,
       unbalanced markers
====================================================================================
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-07

_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX = _ROOT / "index.html"
DEFAULT_MANIFEST = _ROOT / "outputs" / "pipeline_manifest.json"

# marker key -> how to pull the value out of the manifest
_KEYS = {
    "total": lambda m: m["total_registered"],
    "analytical": lambda m: m["analytical_headline"],
    "phases": lambda m: m["analytical_phases"],
    "display": lambda m: m["by_tier"]["display_utility"],
}


def _fail(msg: str) -> None:
    print(f"  x {msg}", file=sys.stderr)
    sys.exit(2)


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        _fail(f"manifest not found: {path}\n"
              f"    run the pipeline, or `python run_analysis.py --manifest-only`")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _fail(f"manifest is not valid JSON: {exc}")
    values = {}
    for key, getter in _KEYS.items():
        try:
            values[key] = int(getter(manifest))
        except (KeyError, TypeError, ValueError):
            _fail(f"manifest has no usable value for '{key}' — "
                  f"has run_analysis.py's manifest schema changed?")
    return values


def stamp(html: str, values: dict[str, int]) -> tuple[str, list[str]]:
    """Rewrite marker contents. Returns (new_html, list of change descriptions)."""
    changes: list[str] = []

    for key, new in values.items():
        pattern = re.compile(
            rf"(<!--PL:{re.escape(key)}-->)(.*?)(<!--/PL:{re.escape(key)}-->)",
            re.DOTALL,
        )
        opens = html.count(f"<!--PL:{key}-->")
        closes = html.count(f"<!--/PL:{key}-->")
        if opens != closes:
            _fail(f"unbalanced markers for '{key}': "
                  f"{opens} opening, {closes} closing")
        if opens == 0:
            continue

        seen: list[str] = []

        def _sub(match: re.Match) -> str:
            old = match.group(2)
            seen.append(old)
            return f"{match.group(1)}{new}{match.group(3)}"

        html = pattern.sub(_sub, html)
        stale = sorted({s for s in seen if s != str(new)})
        if stale:
            changes.append(f"{key}: {', '.join(stale)} -> {new} "
                           f"({len(seen)} site{'s' if len(seen) != 1 else ''})")

    return html, changes


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Stamp index.html's pipeline counts from pipeline_manifest.json.")
    ap.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--check", action="store_true",
                    help="report only; exit 1 if index.html is stale")
    args = ap.parse_args()

    if not args.index.is_file():
        _fail(f"index.html not found: {args.index}")

    values = load_manifest(args.manifest)
    original = args.index.read_text(encoding="utf-8")

    total_markers = sum(original.count(f"<!--PL:{k}-->") for k in _KEYS)
    if total_markers == 0:
        _fail(f"no PL markers found in {args.index.name} — "
              f"has it been replaced by an unmarkered copy?")

    updated, changes = stamp(original, values)

    if not changes:
        print(f"  OK index.html counts already current "
              f"({total_markers} marker sites, "
              f"{values['total']}/{values['analytical']}/{values['phases']}/"
              f"{values['display']})")
        return 0

    if args.check:
        print("  x index.html counts are stale:")
        for line in changes:
            print(f"      {line}")
        return 1

    args.index.write_text(updated, encoding="utf-8")
    print("  OK index.html counts updated:")
    for line in changes:
        print(f"      {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
