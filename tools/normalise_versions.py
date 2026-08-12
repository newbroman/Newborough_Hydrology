#!/usr/bin/env python3
"""
====================================================================================
normalise_versions.py — CONSOLE VERSION REPORTING AUDIT AND REPAIR
====================================================================================
Purpose:
    Every pipeline script declares a module version as `__version__` and
    announces it at run time through `console_utils.banner()`. Those two have
    drifted: many scripts pass a hard-typed string literal to banner() that was
    correct when written and was never updated alongside `__version__`, and many
    others pass no version at all. The console therefore under-reports which
    version of a script actually ran — which matters most when comparing a run
    on Martin's machine against John's.

    This tool makes banner() read `__version__` in every script, so the literal
    cannot drift again.

What it changes:
    1. banner(..., version="1.2.3")  ->  banner(..., version=__version__)
    2. banner("NN", "Title")         ->  banner("NN", "Title", version=__version__)

    Nothing else. No behaviour changes: banner() is console output only.

    3. With --introduce-version, a script that has banner() calls but no
       `__version__` constant is given one at 1.0.0, inserted after the module
       docstring, with a comment recording that 1.0.0 marks the constant's
       introduction and not the start of the module's history. Per Martin's
       ruling, 2026-08-12. Without the flag such scripts are reported and
       skipped.

What it deliberately does NOT change:
    Calls that pass a version in a position the tool does not understand are
    reported, never rewritten. `gen_grid_lay.py` passes __version__ as the
    *title* argument — a pre-existing defect that a sweep must not paper over.

Method:
    Call sites are located with `ast`, not regex — banner() calls span multiple
    lines in places (Script 10m), and the module headers contain prose that
    mentions banner() and version literals (Script 12's changelog block). A
    regex sweep would corrupt both. Edits are applied by byte offset, last call
    first, so earlier offsets stay valid.

Usage:
    python3 tools/normalise_versions.py                 # dry run, report only
    python3 tools/normalise_versions.py --apply         # write changes
    python3 tools/normalise_versions.py --apply --introduce-version

    Idempotent: a second --apply run reports zero changes.

Exit codes:
    0  clean, or changes applied successfully
    1  a rewritten file failed to re-parse (nothing written for that file)
====================================================================================
"""

from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-12

import argparse
import ast
import re
import sys
from pathlib import Path

_VERSION_ASSIGN = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.M)


def module_version(source: str) -> str | None:
    """Return the module's declared __version__, or None if it has none."""
    m = _VERSION_ASSIGN.search(source)
    return m.group(1) if m else None


_VERSION_BLOCK = """__version__ = "1.0.0"  # Hollingham (2026) — {date}
#
# This module previously carried no __version__ constant; 1.0.0 marks its
# introduction, not the start of the module's history. Prior revisions are the
# dated notes and changelog entries elsewhere in the repository.
"""


def introduce_version(source: str, path: Path, date: str) -> str | None:
    """Insert a `__version__ = "1.0.0"` block after the module docstring.

    Returns the updated source, or None if a safe insertion point cannot be
    identified. Placement is taken from the ast so that the constant lands
    after the docstring and after any `from __future__` import, never inside
    a triple-quoted header.
    """
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return None

    insert_after = 0
    body = tree.body
    if body and isinstance(body[0], ast.Expr) and \
            isinstance(body[0].value, ast.Constant) and \
            isinstance(body[0].value.value, str):
        insert_after = body[0].end_lineno
    for node in body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            insert_after = max(insert_after, node.end_lineno)

    lines = source.splitlines(keepends=True)
    block = _VERSION_BLOCK.format(date=date)
    return "".join(lines[:insert_after]) + "\n" + block + "\n" + \
        "".join(lines[insert_after:])


def find_banner_calls(source: str, path: Path) -> list[ast.Call]:
    """Return every `banner(...)` Call node in the module.

    Uses ast so that banner() mentions inside comments and docstrings are
    invisible, and multi-line calls are captured whole.
    """
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise RuntimeError(f"{path}: will not parse ({exc})") from exc

    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "banner":
            calls.append(node)
    return calls


def _byte_offset(lines: list[bytes], lineno: int, col: int) -> int:
    """Absolute byte offset of (1-based lineno, 0-based utf-8 col)."""
    return sum(len(l) for l in lines[: lineno - 1]) + col


def plan_edits(source: str, calls: list[ast.Call]) -> list[tuple[int, int, str, str]]:
    """Return (start, end, replacement, description) byte-range edits.

    ast column offsets are utf-8 byte offsets, so all slicing is done on the
    encoded source. These files contain em-dashes and Greek betas; character
    offsets would be wrong.
    """
    raw = source.encode("utf-8")
    lines = source.splitlines(keepends=True)
    lines_b = [l.encode("utf-8") for l in lines]

    edits: list[tuple[int, int, str, str]] = []
    for call in calls:
        kw = next((k for k in call.keywords if k.arg == "version"), None)

        # banner(script_id, title, version) — a third positional argument IS
        # the version. Appending a version= keyword alongside it would raise
        # "multiple values for argument 'version'" at run time, which neither
        # py_compile nor ast.parse would catch. Scripts 31, 31b, 32, 33, 34,
        # 35 and 38 all call it this way.
        if kw is None and len(call.args) >= 3:
            third = call.args[2]
            if isinstance(third, ast.Constant) and isinstance(third.value, str):
                start = _byte_offset(lines_b, third.lineno, third.col_offset)
                end = _byte_offset(lines_b, third.end_lineno, third.end_col_offset)
                edits.append((start, end, "__version__",
                              f'positional "{third.value}" -> __version__'))
            # A Name (VERSION, __version__) is already dynamic — leave it.
            continue

        if kw is not None:
            # Already dynamic — nothing to do.
            if isinstance(kw.value, ast.Name) and kw.value.id == "__version__":
                continue
            # Literal string -> __version__
            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                start = _byte_offset(lines_b, kw.value.lineno, kw.value.col_offset)
                end = _byte_offset(lines_b, kw.value.end_lineno, kw.value.end_col_offset)
                edits.append((start, end, "__version__",
                              f'version="{kw.value.value}" -> version=__version__'))
                continue
            # Anything else (an f-string, a lookup) is left alone.
            continue

        # No version keyword and fewer than three positionals. If a version-ish
        # Name is already being passed in a position we do not understand, the
        # call is non-standard — report rather than guess. gen_grid_lay.py
        # passes __version__ as the *title* argument, a pre-existing defect that
        # this tool must not paper over.
        if any(isinstance(a, ast.Name) and a.id in {"VERSION", "__version__"}
               for a in call.args):
            edits.append((-1, -1, "",
                          "non-standard banner() call passes a version in an "
                          "unexpected position — left for a human"))
            continue

        # No version keyword at all — insert one before the closing paren.
        end = _byte_offset(lines_b, call.end_lineno, call.end_col_offset)
        close = raw.rfind(b")", 0, end)
        if close == -1:
            continue
        # Preserve a trailing comma style if the call already uses one.
        before = raw[:close].rstrip()
        insert = "version=__version__" if before.endswith(b",") \
            else ", version=__version__"
        edits.append((close, close, insert, "added version=__version__"))

    # Apply last-first so earlier offsets remain valid.
    return sorted(edits, key=lambda e: e[0], reverse=True)


def apply_edits(source: str, edits) -> str:
    raw = bytearray(source.encode("utf-8"))
    for start, end, replacement, _ in edits:
        if start < 0:          # report-only marker, nothing to splice
            continue
        raw[start:end] = replacement.encode("utf-8")
    return raw.decode("utf-8")


def process(path: Path, apply: bool, introduce: bool = False,
            date: str = "2026-08-12") -> tuple[str, list[str]]:
    """Return (status, messages) for one file."""
    source = path.read_text(encoding="utf-8")

    if "banner(" not in source:
        return "skip", []

    declared = module_version(source)
    calls = find_banner_calls(source, path)
    if not calls:
        return "skip", []

    introduced_msg: list[str] = []
    if declared is None:
        if not introduce:
            return "noversion", [
                "has banner() calls but no __version__ constant — rerun with "
                "--introduce-version to add one at 1.0.0; skipped"
            ]
        updated = introduce_version(source, path, date)
        if updated is None:
            return "noversion", ["could not find a safe insertion point for "
                                 "__version__; skipped"]
        source = updated
        introduced_msg = ['introduced __version__ = "1.0.0"']
        calls = find_banner_calls(source, path)

    edits = plan_edits(source, calls)
    if not edits and not introduced_msg:
        return "clean", []

    messages = introduced_msg + [d for *_, d in reversed(edits)]

    if edits and all(start < 0 for start, *_ in edits) and not introduced_msg:
        return "noversion", messages

    if apply:
        updated = apply_edits(source, edits)
        try:
            ast.parse(updated, filename=str(path))
        except SyntaxError as exc:
            return "broken", [f"rewrite failed to re-parse ({exc}) — NOT written"]
        path.write_text(updated, encoding="utf-8")

    return "changed", messages


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Make banner() read __version__ across the pipeline.")
    ap.add_argument("--src", default="src",
                    help="directory to sweep (default: src)")
    ap.add_argument("--apply", action="store_true",
                    help="write changes; without this the run is a dry run")
    ap.add_argument("--introduce-version", action="store_true",
                    help='add __version__ = "1.0.0" to scripts that have '
                         "banner() calls but no version constant")
    args = ap.parse_args()

    root = Path(args.src)
    if not root.is_dir():
        print(f"error: {root} is not a directory")
        return 1

    paths = sorted(p for p in root.rglob("*.py")
                   if "__pycache__" not in p.parts)

    changed = noversion = broken = clean = 0
    print(f"{'DRY RUN — no files written' if not args.apply else 'APPLYING CHANGES'}"
          f"   ({len(paths)} python files under {root}/)\n")

    for path in paths:
        try:
            status, messages = process(path, args.apply,
                                       introduce=args.introduce_version)
        except RuntimeError as exc:
            print(f"  ERROR  {exc}")
            broken += 1
            continue

        rel = path.relative_to(root)
        if status == "changed":
            changed += 1
            print(f"  {'FIXED ' if args.apply else 'WOULD '} {rel}")
            for m in messages:
                print(f"           {m}")
        elif status == "noversion":
            noversion += 1
            print(f"  MANUAL  {rel}")
            for m in messages:
                print(f"           {m}")
        elif status == "broken":
            broken += 1
            print(f"  BROKEN  {rel}")
            for m in messages:
                print(f"           {m}")
        elif status == "clean":
            clean += 1

    print(f"\n  already correct : {clean}")
    print(f"  {'changed' if args.apply else 'would change'} : {changed}")
    print(f"  need a version number by hand : {noversion}")
    if broken:
        print(f"  FAILED : {broken}")

    if not args.apply and changed:
        print("\n  Re-run with --apply to write these changes.")

    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
