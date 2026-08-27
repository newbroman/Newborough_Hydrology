#!/usr/bin/env python3
"""
output_lag.py — is any script's code newer than the outputs it committed?

WHY THIS EXISTS

  `export_lag.py` asks whether each published PDF is newer than the ODT it was
  built from. Nothing asked the same question one layer down: whether a pipeline
  script has changed since the CSVs and figures in `outputs/` were produced.

  So a script could be edited, committed and pushed while the numbers the corpus
  quotes still came from the previous version, and every gate stayed green. That
  is not hypothetical. On 2026-08-27 `15_depth_dependent_pet.py` was renamed λ to
  κ — including two committed CSV column headers — and the only thing that
  noticed was a check written the same afternoon for a different reason. The
  rerun happened because someone remembered.

  Martin, the third time he ran the sequence by hand: *"shouldnt these be in the
  nrg_git script."*

WHY GIT TIMES, NOT MTIMES

  `export_lag` reports "STALE? by modification time only — unreliable after a
  git checkout", and it is right to hedge: a checkout rewrites every mtime, so
  mtime comparison invents staleness on a fresh clone.

  This uses `git log -1 --format=%ct` on each path, which survives a checkout,
  and falls back to mtime only for a path with uncommitted changes — where mtime
  is the honest answer, because there is no commit to ask about.

DOCS-ONLY vs CODE CHANGED

  First run flagged eleven scripts. Seven of them had been touched only by the
  T-11 to T-14 documentation sweeps — comment and docstring edits, incapable of
  moving a number. A tool that asks for eleven pipeline reruns to fix seven
  comment edits is a tool people learn to skip, which is how `check_all` came to
  have gates nobody read.

  So each flagged script is compared to its pre-output version by **AST**, with
  docstrings and `__version__` stripped. Identical trees means nothing that can
  execute has changed, and the flag is DOCS ONLY. Eleven became four.

  It still cannot tell a coefficient change from a variable rename. That
  judgement stays with the person, which is why nothing here gates.

Usage
    python3 tools/output_lag.py            report; exit 0 always
    python3 tools/output_lag.py --quiet    print only if something is behind
    python3 tools/output_lag.py --gate     exit 1 when something is behind
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-27.

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "notes" / "ledgers" / "SCRIPT_LEDGER.md"
OUTPUTS = REPO / "outputs"

C_Y, C_R, C_N = "\033[33m", "\033[31m", "\033[0m"


def _git_time(rel: str) -> int | None:
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%ct", "--", rel],
                             cwd=REPO, capture_output=True, text=True,
                             timeout=20).stdout.strip()
        return int(out) if out else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _dirty() -> set[str]:
    try:
        out = subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                             capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return set()
    return {ln[3:].strip() for ln in out.splitlines() if ln[3:].strip()}


def when(path: Path, dirty: set[str]) -> tuple[int | None, bool]:
    """(timestamp, uncommitted). Commit time normally; mtime when uncommitted."""
    rel = path.relative_to(REPO).as_posix()
    if rel in dirty:
        try:
            return int(path.stat().st_mtime), True
        except OSError:
            return None, True
    return _git_time(rel), False


def _executable_signature(src: str) -> str | None:
    """The AST with docstrings and __version__ removed, as a comparable string.

    A version bump is not a behaviour change and a docstring is not code. Both
    move the file's commit date, and neither is a reason to rerun an hour of
    pipeline.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            b = node.body
            if (b and isinstance(b[0], ast.Expr)
                    and isinstance(b[0].value, ast.Constant)
                    and isinstance(b[0].value.value, str)):
                node.body = b[1:]
    tree.body = [n for n in tree.body
                 if not (isinstance(n, ast.Assign)
                         and any(getattr(t, "id", "") == "__version__"
                                 for t in n.targets))]
    return ast.dump(tree)


def docs_only(script: str, before: int) -> bool | None:
    """Is every change to `src/<script>` since `before` docstring or comment?

    None when it cannot be decided — no earlier commit, or either version does
    not parse. Undecidable is reported as CODE CHANGED: the safe direction is
    asking for a rerun that turns out to be unnecessary.
    """
    rel = f"src/{script}"
    try:
        sha = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--before", str(before),
             "--", rel], cwd=REPO, capture_output=True, text=True,
            timeout=20).stdout.strip()
        if not sha:
            return None
        old = subprocess.run(["git", "show", f"{sha}:{rel}"], cwd=REPO,
                             capture_output=True, text=True,
                             timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    new_p = REPO / rel
    try:
        new = new_p.read_text(encoding="utf8")
    except OSError:
        return None
    a, b = _executable_signature(old), _executable_signature(new)
    return None if (a is None or b is None) else (a == b)


def ledger_rows() -> list[tuple[str, list[str]]]:
    """[(script filename, [emitted artefact names])] from the script ledger."""
    if not LEDGER.exists():
        sys.exit(f"no ledger at {LEDGER.relative_to(REPO)}")
    rows = []
    for line in LEDGER.read_text(encoding="utf8").splitlines():
        if not line.startswith("|"):
            continue
        c = [x.strip() for x in line.split("|")]
        if len(c) < 10 or c[1] in ("#", "") or set(c[1]) <= set("-: "):
            continue
        script = c[2]
        if not script.endswith(".py"):
            continue
        emits = []
        for cell in (c[5], c[6]):          # Emits (data), Emits (figs)
            for tok in re.split(r"[,;]", cell):
                tok = tok.strip().strip("*`")
                # Ledger cells carry prose too ("none", "-", "via render_utils").
                if re.fullmatch(r"[\w./-]+\.(csv|png|jpg|json|txt|geojson|html)",
                                tok):
                    emits.append(tok)
        rows.append((script, emits))
    return rows


def resolve(name: str) -> Path | None:
    if "/" in name:
        p = REPO / name
        return p if p.exists() else None
    hits = list(OUTPUTS.rglob(name))
    return hits[0] if len(hits) == 1 else (hits[0] if hits else None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--gate", action="store_true")
    a = ap.parse_args()

    dirty = _dirty()
    behind, unresolved, no_emits = [], [], []

    for script, emits in ledger_rows():
        sp = REPO / "src" / script
        if not sp.exists():
            continue
        s_t, s_dirty = when(sp, dirty)
        if s_t is None:
            continue
        if not emits:
            no_emits.append(script)
            continue
        # NEWEST output, not oldest. Git records a commit for a file only when
        # its CONTENT changed, so an artefact a rerun regenerated byte-identical
        # keeps its old commit date. Comparing against the oldest therefore
        # flagged 35 of 68 scripts on first run — every one of them a script
        # with at least one stable output. The question this tool asks is "has
        # ANY run happened since the edit?", and that is the newest.
        newest = None
        missing = []
        for name in emits:
            op = resolve(name)
            if op is None:
                missing.append(name)
                continue
            o_t, _ = when(op, dirty)
            if o_t is not None and (newest is None or o_t > newest[0]):
                newest = (o_t, name)
        if missing:
            unresolved.append((script, missing))
        if newest and s_t > newest[0]:
            behind.append((script, s_dirty, newest[1],
                           (s_t - newest[0]) / 86400.0,
                           docs_only(script, newest[0])))

    code = [r for r in behind if r[4] is not True]
    docs = [r for r in behind if r[4] is True]

    if code:
        print(f"  {C_R}output_lag{C_N}: {len(code)} script(s) whose CODE changed "
              f"since their outputs were produced — rerun before quoting their "
              f"numbers")
        for script, s_dirty, out, days, _ in sorted(code, key=lambda r: -r[3]):
            mark = "uncommitted" if s_dirty else f"{days:.1f} d ahead"
            print(f"    python3 src/{script:32s} {mark:14s} newest: {out}")
    if docs and not a.quiet:
        print(f"  output_lag: {len(docs)} script(s) ahead of their outputs by "
              f"docstring or comment only — no rerun owed:")
        print("    " + ", ".join(sorted(r[0] for r in docs)))
    if not behind and not a.quiet:
        print("  output_lag: OK — every script's outputs are at least as new "
              "as its code")

    if unresolved and not a.quiet:
        n = sum(len(m) for _, m in unresolved)
        print(f"  output_lag: {n} ledger artefact(s) not found under outputs/ "
              f"across {len(unresolved)} script(s) — advisory, the ledger names "
              f"them and the run has not produced them")

    return 1 if (code and a.gate) else 0


if __name__ == "__main__":
    sys.exit(main())
