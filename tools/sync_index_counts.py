#!/usr/bin/env python3
"""
====================================================================================
sync_index_counts.py — stamp index.html's pipeline counts from the manifest
====================================================================================

Purpose:
    index.html and PIPELINE_README.md are hand-maintained and state the pipeline
    step counts in prose. (Until 2026-09-09 this docstring claimed index.html was
    the ONLY such document. It was not: a sweep that day found the counts typed
    in seven places at FOUR different vintages — 43 in the Welsh summary, 52 in
    the English summary and PIPELINE_README, 53 in four report chapters, 54 in
    the Methods Supplement and here. Every one of them also said, in the same
    sentence, that the canonical count lives in the manifest.)
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

        PL:total        total_registered              registered orchestrator steps
        PL:phases       total_phases                  phases in the orchestrator
        PL:analytical   by_tier.analytical_toplevel   tier-A steps
        PL:display      by_tier.display_utility       tier-D steps
        PL:diagnostic   by_tier.optin_diagnostic      tier-X steps
        PL:default      by_exec.default               steps a default pass runs
        PL:optin        by_exec.optin                 --with-supplementary only

    NOTE on the two axes. The tier keys (analytical / display / diagnostic)
    and the exec keys (default / optin) are two INDEPENDENT partitions of the
    same total_registered steps. Each axis sums to the total on its own;
    the two must never be added to one another. Prose of the form "N steps,
    of which A are analytical and D display/utility" mixes the axes and will
    not sum — that sentence stood on this page until 2026-08-09.

    v1.1.0 of this script mapped PL:analytical to the manifest's
    "analytical_headline" and PL:phases to "analytical_phases". The former was
    a hand-maintained constant reconciling with nothing and was deleted in
    run_analysis.py v2.3.0; the latter is now derived and equals 15, not the
    total 17 this page means. Both keys were remapped accordingly.

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

__version__ = "1.4.0"  # Hollingham (2026) — 2026-09-24
# 1.4.0 — counts that are not pipeline counts. Martin, on the audit note's line
#         "the same sweep is worth repeating when a rename lands": "if this is the
#         case then it needs to be included as a gate". So: (a) DERIVED keys read
#         from the tree beside the manifest keys — pins (requirements.txt),
#         ledgers (notes/ledgers), doc_links (index.html), report_figures
#         (FIGURE_LEDGER), report_tables (PROVENANCE_LEDGER), decisions
#         (DECISIONS_PUBLIC), wells_reference / wells_extended / wells_total
#         (the 01 CSVs) — so any of them can sit in a marker; (b) --check also
#         runs audit_counts() over AUDIT_DOCS and FAILS on a number-plus-noun
#         claim ("nineteen packages", "47 figures", "57 steps") that is outside a
#         marker and on a line carrying no date: a dated count is testimony, an
#         undated one is a claim, and a claim has to be a marker or an exemption
#         (tools/count_claims_exempt.csv, with a reason). --check now gates in
#         check_all; until today the stamp ran only when someone remembered.
# 1.3.0 — readme.md joins DEFAULT_TARGETS. The 2026-09-24 documentation audit
#         found it carrying 57/52/18/43 in five places — the counts this tool
#         has stamped into index.html and PIPELINE_README since 2026-08-09,
#         hand-typed once more in the file nobody wrapped. Every count in
#         readme.md is now inside a PL marker.
# 1.2.0 — remapped to the run_analysis.py v2.3.0 manifest schema. PL:analytical
#         read "analytical_headline", a hand-maintained constant now deleted;
#         reading it after the schema change would have exited 2. It now reads
#         by_tier.analytical_toplevel. PL:phases moved from "analytical_phases"
#         (now derived, = 15) to "total_phases" (= 17), which is what index.html
#         means by "phases". Added PL:diagnostic, PL:default and PL:optin so both
#         partitions can be stamped. Deleted the docstring paragraph asserting
#         that "46 analytical + 4 display/utility" against a total of 49 was not
#         an arithmetic error — it was; the two figures sat on different axes.
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
# Every hand-maintained file carrying PL markers. Both are plain text in the
# repository, so they can be STAMPED. The ODT-backed documents cannot be, and
# are gated instead by tools/pipeline_count_lint.py.
DEFAULT_TARGETS = (_ROOT / "index.html", _ROOT / "PIPELINE_README.md", _ROOT / "readme.md", _ROOT / "CLAUDE.md")
DEFAULT_MANIFEST = _ROOT / "outputs" / "pipeline_manifest.json"

# marker key -> how to pull the value out of the manifest
_KEYS = {
    "total": lambda m: m["total_registered"],
    "phases": lambda m: m["total_phases"],
    "analytical": lambda m: m["by_tier"]["analytical_toplevel"],
    "display": lambda m: m["by_tier"]["display_utility"],
    "diagnostic": lambda m: m["by_tier"]["optin_diagnostic"],
    "default": lambda m: m["by_exec"]["default"],
    "optin": lambda m: m["by_exec"]["optin"],
}


AUDIT_DOCS = ("CLAUDE.md", "MACHINE_SETUP.md", "readme.md", "PIPELINE_README.md",
              "index.html", "notes/ledgers/README.md", "literature/README.md",
              "working/HANDOVER_BOOTSTRAP.md", "working/README_WORKING.md",
              "working/WORK_REGISTER.md")
COUNT_EXEMPT = _ROOT / "tools" / "count_claims_exempt.csv"


def _count_lines(path: Path, pattern: str) -> int:
    if not path.is_file():
        return 0
    return len(re.findall(pattern, path.read_text(encoding="utf-8", errors="replace"), flags=re.M))


def _csv_columns(path: Path) -> int:
    if not path.is_file():
        return 0
    header = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    return len(header.split(",")) - 1              # minus the date column


def _report_figures() -> int:
    p = _ROOT / "notes/ledgers/FIGURE_LEDGER.md"
    m = re.search(r"\*\*(\d+) report figures\*\*", p.read_text(encoding="utf-8")) if p.is_file() else None
    return int(m.group(1)) if m else 0


def _report_tables() -> int:
    p = _ROOT / "notes/ledgers/PROVENANCE_LEDGER.md"
    return len(set(re.findall(r"Table 1\.\d+", p.read_text(encoding="utf-8")))) if p.is_file() else 0


def _ledgers() -> int:
    """Live ledger files under notes/ledgers (RETIRED banners excluded; one per family)."""
    n = 0
    for p in sorted((_ROOT / "notes/ledgers").glob("*.md")):
        if p.name == "README.md" or "_report" in p.name:
            continue
        head = p.read_text(encoding="utf-8", errors="replace")[:400]
        if "RETIRED" in head.upper() and "retired" in p.read_text(encoding="utf-8", errors="replace")[:200].lower():
            continue
        n += 1
    return n


# Derived keys: read from the tree, not the manifest. Each is a count a root
# document has typed by hand and got wrong at least once (see the 1.4.0 note).
_DERIVED = {
    "pins": lambda: _count_lines(_ROOT / "requirements.txt", r"^[A-Za-z0-9_.-]+=="),
    "ledgers": _ledgers,
    "doc_links": lambda: _count_lines(_ROOT / "index.html", r'class="doc-link"'),
    "report_figures": _report_figures,
    "report_tables": _report_tables,
    "decisions": lambda: _count_lines(_ROOT / "DECISIONS_PUBLIC.md", r"^### D-\d{3}"),
    "wells_reference": lambda: _csv_columns(_ROOT / "outputs/01_wells_reference.csv"),
    "wells_extended": lambda: _csv_columns(_ROOT / "outputs/01_wells_extended.csv"),
    "wells_total": lambda: _csv_columns(_ROOT / "outputs/01_wells_reference.csv")
                           + _csv_columns(_ROOT / "outputs/01_wells_extended.csv"),
    "wells_dist_coast": lambda: max(0, _count_lines(_ROOT / "outputs/01_dist_coast_validation.csv", r"^.+$") - 1),
}

COUNT_NOUNS = (r"(?:registered\s+)?steps|phases|packages|pins|ledgers|documents|figures|tables|decisions|"
               r"gates|dipwells|wells|reference\s+wells|extended\s+wells|entries")
# A count under ten ("five wells (CEH3, …)", "two figures") is a list the sentence
# then gives, not a total that drifts; the class this gates is the total.
COUNT_MIN = 10
_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
    "fifteen sixteen seventeen eighteen nineteen twenty".split())}
COUNT_RE = re.compile(r"(?<![\w.])(\d{1,3}|" + "|".join(_WORDS) + r")\s+(?:(?:registered|live|generated|report|pipeline|reference|extended|open|analytical|display|diagnostic|opt-in|default|CCW|dated|tracked|committed)\s+)?(" + COUNT_NOUNS + r")\b", re.I)
DATE_RE = re.compile(r"\b20\d\d-\d\d(?:-\d\d)?\b|\bon \d{1,2} [A-Z][a-z]+\b|\buntil\b|\bsince\b|\bwas\b|\bwere\b|\bused to\b|\bhad\b")


def _load_count_exempt() -> dict[str, str]:
    if not COUNT_EXEMPT.is_file():
        return {}
    import csv
    with COUNT_EXEMPT.open(encoding="utf-8", newline="") as f:
        return {r["claim"].strip(): r["reason"].strip() for r in csv.DictReader(f) if r.get("claim")}


def audit_counts() -> list[str]:
    """Number-plus-noun claims outside markers, on undated lines, in the root documents."""
    exempt = _load_count_exempt()
    hits: list[str] = []
    for rel in AUDIT_DOCS:
        p = _ROOT / rel
        if not p.is_file():
            continue
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            scrubbed = re.sub(r"<!--PL:(\w+)-->.*?<!--/PL:\1-->", "\0", line)
            if DATE_RE.search(scrubbed) or "<!-- former" in scrubbed:
                continue
            for m in COUNT_RE.finditer(scrubbed):
                num = m.group(1).lower()
                value = int(num) if num.isdigit() else _WORDS.get(num, 0)
                if value < COUNT_MIN or scrubbed[max(0, m.start()-1):m.start()] == "~":
                    continue
                claim = f"{m.group(1)} {m.group(2)}"
                if claim in exempt or f"{rel}:{claim}" in exempt:
                    continue
                # "step 47", "Scripts 22–24", "Phase 16" are IDs (noun first); this
                # pattern is number-first, so those do not reach here. A range
                # "42–49" before "steps" is a span, not a count.
                if re.search(r"[\u2013-]\s*$", scrubbed[:m.start()]):
                    continue
                hits.append(f"  {rel}:{n}  '{claim}'  …{scrubbed[max(0, m.start()-40):m.end()+30].strip()}…")
    return hits


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


def _summarise(values: dict[str, int]) -> str:
    """One-line rendering of every stamped value, both axes kept apart."""
    return (f"{values['total']} steps / {values['phases']} phases; "
            f"tier {values['analytical']}A+{values['display']}D+"
            f"{values['diagnostic']}X; "
            f"exec {values['default']}+{values['optin']} opt-in")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Stamp index.html's pipeline counts from pipeline_manifest.json.")
    ap.add_argument("--index", type=Path, default=None,
                    help="stamp only this file (default: every PL-marked target)")
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--check", action="store_true",
                    help="report only; exit 1 if any target is stale")
    args = ap.parse_args()

    targets = [args.index] if args.index else list(DEFAULT_TARGETS)
    values = load_manifest(args.manifest)
    for key, fn in _DERIVED.items():
        values[key] = int(fn())
    rc = 0

    for target in targets:
        if not target.is_file():
            _fail(f"target not found: {target}")
        original = target.read_text(encoding="utf-8")

        total_markers = sum(original.count(f"<!--PL:{k}-->") for k in values)
        if total_markers == 0:
            _fail(f"no PL markers found in {target.name} — "
                  f"has it been replaced by an unmarkered copy?")

        updated, changes = stamp(original, values)
        # The unmanaged audit is written for index.html, a page with a handful of
        # numbers in prose. PIPELINE_README is a script-by-script reference that
        # names a step number on nearly every line, so the same audit returns
        # ~286 hits there — all of them step IDs, none of them totals. A warning
        # that cries wolf 286 times is a warning nobody reads, so it is scoped to
        # the page it was written for.
        unmanaged = audit_unmanaged(original) if target.suffix == ".html" else []

        if not changes:
            print(f"  OK {target.name} counts already current "
                  f"({total_markers} marker sites; {_summarise(values)})")
            _report_unmanaged(unmanaged)
            continue

        if args.check:
            print(f"  x {target.name} counts are stale:")
            for line in changes:
                print(f"      {line}")
            _report_unmanaged(unmanaged)
            rc = 1
            continue

        target.write_text(updated, encoding="utf-8")
        print(f"  OK {target.name} counts updated:")
        for line in changes:
            print(f"      {line}")
        _report_unmanaged(unmanaged)

    if args.check:
        hits = audit_counts()
        if hits:
            print(f"  x {len(hits)} count claim(s) in the root documents are neither markered, "
                  f"dated nor exempt:")
            print(*hits, sep="\n")
            print("      (wrap in <!--PL:key-->N<!--/PL:key-->, date the sentence, or add the claim to "
                  "tools/count_claims_exempt.csv with a reason)")
            rc = 1
        else:
            print("  OK no undated, unmarkered count claims in the root documents")
    return rc


if __name__ == "__main__":
    sys.exit(main())
