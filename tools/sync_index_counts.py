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

__version__ = "1.1.0"  # Hollingham (2026) — 2026-08-07
# 1.1.0 — added audit_unmanaged(). v1.0.0 markered four sites and reported
#         "already current" while a fifth, "<strong>43</strong>
#         <span>pipeline steps</span>", sat unmarkered and three counts out of
#         date. The number and its noun were separated by markup, so the
#         search that found the other sites missed it; "A 46-step ... pipeline"
#         was missed for the same reason (hyphen, not space). The audit now
#         warns about any two-digit number near "step" or "phase" that is not
#         inside a marker pair, so a newly added or overlooked site is
#         reported rather than silently going stale.

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


def _report_unmanaged(warnings: list[str]) -> None:
    """Print the unmarkered-number warnings, if any. Never changes the exit code."""
    if not warnings:
        return
    print(f"  ! {len(warnings)} step-like number(s) outside the markers "
          f"- these will NOT be kept in step:")
    for line in warnings:
        print(f"      {line}")
    print("      (wrap in <!--PL:key-->N<!--/PL:key--> if they are pipeline counts)")


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


def audit_unmanaged(html: str) -> list[str]:
    """
    Warn about step-like numbers that sit OUTSIDE the markers.

    Stamping only touches markered sites, so an unmarkered number is invisible
    to this script and will go stale unnoticed — which is exactly what happened
    to the "43 pipeline steps" stat chip. Deliberately narrow: two-digit numbers
    only, within 60 characters of "step" or "phase", outside <style>, and not
    part of a --from/step N command example.
    """
    # blank out managed regions and the stylesheet so neither can false-positive
    scrubbed = re.sub(r"<!--PL:(\w+)-->.*?<!--/PL:\1-->", "\0", html, flags=re.DOTALL)
    scrubbed = re.sub(r"<style.*?</style>", lambda m: " " * len(m.group(0)),
                      scrubbed, flags=re.DOTALL | re.IGNORECASE)

    warnings: list[str] = []
    for match in re.finditer(r"\b\d{2}\b", scrubbed):
        before = scrubbed[max(0, match.start() - 60):match.start()]
        after = scrubbed[match.end():match.end() + 60]
        if not re.search(r"step|phase", before + after, re.IGNORECASE):
            continue
        # command examples: "--from 14", "resume from step 14"
        if re.search(r"(--from|step)\s*$", before):
            continue
        # version numbers: the "10" of "Python 3.10+"
        if before.endswith(".") or scrubbed[match.end():match.end() + 1] == ".":
            continue
        line = scrubbed[:match.start()].count("\n") + 1
        context = " ".join((before[-45:] + "[" + match.group(0) + "]"
                            + after[:45]).split())
        warnings.append(f"line {line}: {context}")
    return warnings


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
    unmanaged = audit_unmanaged(original)

    if not changes:
        print(f"  OK index.html counts already current "
              f"({total_markers} marker sites, "
              f"{values['total']}/{values['analytical']}/{values['phases']}/"
              f"{values['display']})")
        _report_unmanaged(unmanaged)
        return 0

    if args.check:
        print("  x index.html counts are stale:")
        for line in changes:
            print(f"      {line}")
        _report_unmanaged(unmanaged)
        return 1

    args.index.write_text(updated, encoding="utf-8")
    print("  OK index.html counts updated:")
    for line in changes:
        print(f"      {line}")
    _report_unmanaged(unmanaged)
    return 0


if __name__ == "__main__":
    sys.exit(main())
