#!/usr/bin/env python3
"""
ledger_lint.py — does SCRIPT_LEDGER.md still describe the code?

WHAT GOES WRONG WITHOUT IT

  `notes/ledgers/SCRIPT_LEDGER.md` calls itself "the anti-drift spine — read it to know
  the current state without replaying the changelog history", and states its own
  maintenance rule: *every script change updates its row here*. Nothing enforced
  that rule, and on 2026-08-24 the measurement was:

      29 of 67 rows carried a stale version
      2 scripts had no row at all (10n, 39)
      the header still cited HEAD 30aed9b, ten days old

  `25_coastal_gradient` read 1.6.2 against a live 1.17.0. A reader following the
  ledger's own instruction — read this instead of the changelog — would have been
  eleven minor versions out on the script the coastal chapter rests on.

  This is the third record in this project to rot the same way. `citation_index`
  did it until `cite_check`; the decision log did it until `decision_lint`. The
  pattern is not carelessness, it is that A RECORD NOTHING READS IS A RECORD THAT
  ROTS, and the remedy each time was a check rather than a resolution to try
  harder.

WHAT IT CHECKS, AND WHAT IT REFUSES TO CHECK

  GATE — structural faults, which are unambiguous and cheap to fix:
    * a script in src/ with no row (it is invisible to anyone reading the ledger)
    * a row naming a script that no longer exists (it describes nothing)

    * WITNESS (1.2.0, D-325: `committed`) — a script whose EXECUTABLE source differs from
      its committed state while `__version__` reads the same. Every version comparison
      below reads a label the editor writes; this reads the code. Two states of each
      ledger script are compared with the working tree: HEAD (an uncommitted edit), and
      the parent of the last commit that touched it (so the check does not go quiet the
      moment the edit is committed). "Executable source" is code_signature.signature():
      comments, docstrings and the __version__ line removed, so a comment-only edit asks
      for nothing. Cleared by bumping `__version__`, with its changelog line.
      Why not outputs/pipeline_code_signatures.json, which records the code each step
      RAN: the pipeline rewrites it on every run, so the re-run output_lag asks for after
      an edit would erase the evidence of an unbumped one. The function is reused; the
      reference state is git's, which no run and no editor of the script rewrites.
      Not seen: an edit older than a shallow clone's boundary, and src/utils/ (no ledger
      rows; utils/paths.py is a registry that is edited without a bump by practice).

  ADVISORY — version drift. Printed, counted, not gated. Twenty-nine stale rows
  is a maintenance backlog, and a gate that fails from the day it lands is a gate
  someone switches off within the week. The same reasoning check_all already
  applies to pipeline_lint's literal check and to export_lag.

  NOT CHECKED — Consumes, Emits and Cited. Those need a human to read the script,
  and a tool that pretended to verify them would produce exactly the false
  assurance the ledger already suffers from. `--fix-versions` therefore bumps the
  version and sets Status to **DRIFT?**, the ledger's own token for "moved, not
  re-reconciled". It never writes **OK**: only a person who has re-read the
  script's inputs and outputs may do that.

Usage:
    python3 tools/ledger_lint.py                 # report
    python3 tools/ledger_lint.py --quiet         # gate faults only
    python3 tools/ledger_lint.py --fix-versions  # bump Ver, mark Status DRIFT?
    python3 tools/ledger_lint.py --selftest      # the witness fails on an unbumped edit
"""
from __future__ import annotations

__version__ = "1.2.0"  # Hollingham (2026) — 2026-11-24 (D-325, R44). The gate gets a witness: each ledger script's
#   executable source (code_signature.signature) against its COMMITTED state — HEAD, and the parent of the last commit
#   touching it — and a change there with `__version__` unchanged FAILS. Until now nothing compared a code edit with a
#   bump: every check here read the version label the editor writes. Measured on the day over this clone's history:
#   73 committed edits to src/, 3 unbumped, all utils/paths.py (no ledger row, out of scope); 0 on a ledger script.
#   Adds --selftest.
#
# "1.1.0"  # Hollingham (2026) — 2026-09-01. Adds the
#   DOCSTRING VERSION check. Three modules carried a `__version__ :` line inside
#   their module docstring that had drifted from the real assignment, because the
#   bump convention updates one copy and not the other. Nothing downstream was
#   broken — every tool here reads the assignment — but on 2026-09-01 the stale
#   docstring line in 41_canopy_cover.py was read as the live version and a sound
#   ledger row was reported as a defect on the strength of it. A file that states
#   a version it does not have is a trap for the next reader, human or not.
#
# v1.0.0  # Hollingham (2026) — 2026-08-25.

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "notes/ledgers/SCRIPT_LEDGER.md"
SRC = REPO / "src"

# The ledger declares its own exemptions, in prose:
#
#   *(Not rows: `gen_grid_lay.py`, `run_09_scraping.py`, `run_10_clearfell.py`
#     — utility/orchestration.)*
#
# They are READ FROM THE LEDGER rather than copied here. A hard-coded list would
# be a second place the same fact lives, and this project has spent the day
# fixing the consequences of exactly that — a donor pool duplicated beside the
# analysis that reads it, a decision log with two numbering schemes, a mirror
# generator superseded but not retired. The ledger says what it does not cover;
# this tool believes it.
_EXEMPT = re.compile(r"Not rows:(.*?)—", re.S)

# The top-level orchestrator is the one exemption the ledger does not state,
# because it lives outside src/ and never appeared in the scan that built it.
ALWAYS_EXEMPT = {"run_analysis.py"}


def declared_exemptions(text: str) -> set[str]:
    m = _EXEMPT.search(text)
    if not m:
        return set()
    return set(re.findall(r"`([^`]+\.py)`", m.group(1)))

_VER = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.M)


def live_version(script: str) -> str | None:
    p = SRC / script
    if not p.exists():
        return None
    m = _VER.search(p.read_text(encoding="utf-8", errors="ignore"))
    return m.group(1) if m else None


# A version line inside a module docstring, e.g. `__version__ : 2.0.0`. Not an
# assignment — the colon form is prose, and Python never reads it — which is
# exactly why it drifts.
_DOC_VER = re.compile(r'^__version__\s*:\s*([0-9][0-9A-Za-z._-]*)\s*$', re.M)


def docstring_version_drift() -> list[tuple[str, str, str]]:
    """Files whose docstring version line disagrees with the assignment.

    Scans src/ recursively, not just the ledger's rows: two of the three known
    cases were in src/utils/, which has no ledger row and would otherwise never
    be checked.
    """
    out = []
    for p in sorted(SRC.rglob("*.py")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        md = _DOC_VER.search(text)
        if not md:
            continue
        ma = _VER.search(text)
        if not ma:
            continue
        if md.group(1) != ma.group(1):
            out.append((str(p.relative_to(REPO)), md.group(1), ma.group(1)))
    return out


# ---------------------------------------------------------------- the witness (D-325)

def unbumped(old_src: str | None, new_src: str | None) -> str | None:
    """The version both states carry, when the executable source moved between them and it did not. Else None."""
    if old_src is None or new_src is None or old_src == new_src:
        return None
    va, vb = _VER.search(old_src), _VER.search(new_src)
    if not (va and vb and va.group(1) == vb.group(1)):
        return None                                    # the version moved (or there is none): nothing to convict
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import code_signature
    a, b = code_signature.signature(old_src), code_signature.signature(new_src)
    if a is None or b is None or a == b:               # unparseable is another gate's fault; same code = no edit
        return None
    return vb.group(1)


def _git(repo: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def witness(repo: Path, scripts: list[str], src: str = "src") -> tuple[list[str], int, int] | None:
    """(faults, scripts compared with HEAD, of which also with the state before their last commit), or None where
    there is no git history to read."""
    log = _git(repo, "log", "--format=@%H", "--name-only", "--", src)
    if log is None or _git(repo, "rev-parse", "HEAD") is None:
        return None
    last, cur = {}, None                               # path -> the last commit that touched it
    for line in log.splitlines():
        if line.startswith("@"):
            cur = line[1:]
        elif line.strip():
            last.setdefault(line.strip(), cur)
    faults, n, n_base = [], 0, 0
    for s in sorted(scripts):
        rel = f"{src}/{s}"
        p = repo / rel
        if not p.is_file():
            continue
        tree = p.read_text(encoding="utf-8", errors="ignore")
        head = _git(repo, "show", f"HEAD:{rel}")
        c = last.get(rel)
        base = _git(repo, "show", f"{c}^:{rel}") if c else None
        if head is None and base is None:
            continue                                   # a new script: nothing committed to compare with
        n += 1
        n_base += base is not None
        v = unbumped(head, tree)
        if v:
            faults.append(f"{s}: executable source differs from HEAD and __version__ is still {v} "
                          f"(an uncommitted edit without a bump)")
            continue
        v = unbumped(base, tree)
        if v:
            faults.append(f"{s}: executable source changed in {c[:8]} and __version__ is still {v} "
                          f"(a committed edit without a bump)")
    return faults, n, n_base


def selftest() -> int:
    v1 = '"""Doc."""\n__version__ = "1.0.0"  # first\nx = 1\nprint(x)\n'
    comment = v1.replace("x = 1", "x = 1  # one").replace('"""Doc."""', '"""Doc, reworded."""')
    edit = v1.replace("x = 1", "x = 2")
    bumped = edit.replace("1.0.0", "1.0.1")
    bad = []
    if unbumped(v1, edit) != "1.0.0":
        bad.append("an executable edit with the version unchanged was not seen")
    if unbumped(v1, bumped) or unbumped(v1, comment) or unbumped(v1, v1) or unbumped(None, v1) \
            or unbumped(v1, v1.replace("1.0.0", "1.0.1")):
        bad.append("a bumped edit, a comment/docstring-only edit, no edit or a new file read as unbumped")
    # End to end, in a throwaway repository: the fault must fail committed AND uncommitted, and the bump must clear it.
    import os
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        (repo / "src").mkdir()
        f = repo / "src" / "01_a.py"
        env = {"PATH": os.environ["PATH"], "HOME": tmp, "GIT_CONFIG_NOSYSTEM": "1"}

        def g(*args):
            subprocess.run(["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@t",
                            "-c", "commit.gpgsign=false", *args], capture_output=True, text=True, check=True, env=env)

        def commit(text):
            f.write_text(text, encoding="utf-8")
            g("add", "-A")
            g("commit", "-q", "-m", "x")

        g("init", "-q")
        commit(v1)
        if witness(repo, ["01_a.py"]) != ([], 1, 0):
            bad.append("repo: a script with one commit did not read as 'compared with HEAD only'")
        commit(bumped)
        if witness(repo, ["01_a.py"]) != ([], 1, 1):
            bad.append("repo: a committed edit WITH its bump faulted, or was not compared")
        f.write_text(bumped.replace("x = 2", "x = 3"), encoding="utf-8")
        w = witness(repo, ["01_a.py"])
        if not (w and len(w[0]) == 1 and "uncommitted edit without a bump" in w[0][0]):
            bad.append(f"repo: THE FAULT — an uncommitted executable edit, version unchanged — passed: {w}")
        commit(bumped.replace("x = 2", "x = 3"))
        w = witness(repo, ["01_a.py"])
        if not (w and len(w[0]) == 1 and "committed edit without a bump" in w[0][0]):
            bad.append(f"repo: THE FAULT — the same edit once COMMITTED — passed: {w}")
        f.write_text(bumped.replace("x = 2", "x = 3").replace("1.0.1", "1.0.2"), encoding="utf-8")
        if witness(repo, ["01_a.py"]) != ([], 1, 1):
            bad.append("repo: bumping the version did not clear the fault")
        commit(bumped.replace("x = 2", "x = 3  # three").replace("1.0.1", "1.0.2"))
        if witness(repo, ["01_a.py"]) != ([], 1, 1):
            bad.append("repo: a comment-only commit faulted")
    if witness(Path(tempfile.gettempdir()) / "no_such_repo_ledger_lint", ["01_a.py"]) is not None:
        bad.append("no git history did not read as 'cannot compare'")
    if bad:
        print("ledger_lint --selftest: FAIL")
        for b in bad:
            print(f"    - {b}")
        return 1
    print("ledger_lint --selftest: OK")
    return 0


def rows(text: str) -> list[dict]:
    out = []
    for i, line in enumerate(text.split("\n")):
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 8 or cells[1] in ("Script", "--------"):
            continue
        if not cells[1].endswith(".py"):
            continue
        out.append({"line": i, "id": cells[0], "script": cells[1],
                    "ver": cells[2], "status": cells[-1], "cells": cells})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--fix-versions", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    if not LEDGER.exists():
        print(f"  SKIP  {LEDGER.name} not in this checkout")
        return 0

    text = LEDGER.read_text(encoding="utf-8")
    rs = rows(text)
    listed = {r["script"] for r in rs}
    exempt = declared_exemptions(text) | ALWAYS_EXEMPT
    on_disk = {p.name for p in SRC.glob("*.py")} - exempt

    missing = sorted(on_disk - listed)
    orphan = sorted(s for s in listed if not (SRC / s).exists())

    drift = []
    for r in rs:
        live = live_version(r["script"])
        if live is None:
            continue
        # A few rows record a supersession inline, e.g. "1.3.0 (live 1.4.0)".
        # Compare against the first version token only.
        recorded = r["ver"].split()[0].strip("`*")
        if recorded != live:
            drift.append((r, recorded, live))

    fail = 0
    if missing:
        fail = 1
        print(f"  FAIL  {len(missing)} script(s) in src/ with no ledger row:")
        for s in missing:
            print(f"          {s}")
    if orphan:
        fail = 1
        print(f"  FAIL  {len(orphan)} row(s) naming a script that no longer exists:")
        for s in orphan:
            print(f"          {s}")

    docdrift = docstring_version_drift()
    if docdrift:
        fail = 1
        print(f"  FAIL  {len(docdrift)} module(s) whose docstring states a "
              f"version the file does not have:")
        for rel, doc, live in docdrift:
            print(f"          {rel:<40} docstring {doc:<10} assignment {live}")
        print("          The assignment is authoritative and every tool reads it;")
        print("          the docstring line is prose that the bump convention")
        print("          forgets. Correct the docstring, not the assignment.")
    elif not args.quiet:
        print("  docstring version lines agree with their assignments")

    w = witness(REPO, sorted(listed & on_disk))
    if w is None:
        print("  witness: SKIP — no git history here, so no script was compared with its committed state")
    else:
        w_faults, n_cmp, n_base = w
        if w_faults:
            fail = 1
            print(f"  FAIL  {len(w_faults)} script(s) edited without a version bump (witness: committed):")
            for f in w_faults:
                print(f"          {f}")
            print("          Bump __version__ with its dated changelog line, and the ledger row with it.")
            # check_all prints only lines that start "  ledger_lint:" — so the red section names its cause.
            print(f"  ledger_lint: FAIL — edited without a version bump: "
                  f"{', '.join(f.split(':')[0] for f in w_faults)}")
        elif not args.quiet:
            print(f"  witness (committed): {n_cmp} script(s) compared with HEAD, {n_base} also with the state before "
                  f"their last commit; no executable edit without a version bump")

    if not args.quiet or drift:
        print(f"  {len(drift)} row(s) with a stale version "
              f"(advisory — the ledger's own maintenance backlog)")
    if drift and not args.quiet:
        for r, rec, live in drift:
            print(f"      {r['script']:<38} ledger {rec:<10} live {live}")

    if args.fix_versions and drift:
        lines = text.split("\n")
        for r, rec, live in drift:
            cells = r["cells"][:]
            cells[2] = live
            # Never write OK. A version bump says the code moved; it says
            # nothing about whether Consumes/Emits still describe it.
            if not cells[-1].startswith("**DRIFT"):
                cells[-1] = "**DRIFT?**"
            lines[r["line"]] = "| " + " | ".join(cells) + " |"
        LEDGER.write_text("\n".join(lines), encoding="utf-8")
        print(f"\n  bumped {len(drift)} version(s); each row marked **DRIFT?** —")
        print(f"  re-read the script's Consumes/Emits before setting any to OK.")

    if not fail and not args.quiet:
        print(f"  ledger_lint: {len(rs)} rows, every script listed, no orphans "
              f"({len(exempt)} declared exemption(s))")
    if fail:
        print("ledger_lint: FAIL")
    elif args.quiet:
        print("ledger_lint: OK")
    return fail


if __name__ == "__main__":
    raise SystemExit(main())
