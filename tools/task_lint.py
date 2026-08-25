#!/usr/bin/env python3
"""
task_lint.py — outstanding work, where "done" is a command rather than a memory.

WHAT GOES WRONG WITHOUT IT

  This project keeps four registers of state, and every one of them has rotted
  the same way:

      citation_index.csv    119 stale rows      — until cite_check
      DECISION_LOG.md       two numbering schemes — until decision_lint
      SCRIPT_LEDGER.md      29 stale versions, 2 missing scripts — until ledger_lint
      NRG_WORK_REGISTER.md  said 37 easting passages; there were 113

  The pipeline never does this. `run_analysis.py` registers every step, emits
  `pipeline_manifest.json`, and `sync_index_counts` reads it, so a step cannot be
  quietly lost. The editorial side had registers that nothing read, and a record
  nothing reads is a record that rots.

THE DESIGN, WHICH IS ONE IDEA

  **A task has no stored status.** There is no `done` column, because a stored
  status is a claim someone has to remember to update — which is the failure
  above, in miniature. Instead each row carries a CHECK: a command, and the
  output it must produce. Status is computed every run.

  A task therefore closes itself the moment its condition is met, and — more to
  the point — REOPENS ITSELF if the condition stops holding. Marking something
  done that isn't is not possible, because nobody marks anything.

  What cannot be expressed as a check does not belong here. A row that says
  "tidy up the coastal section" is a note, not a task, and notes live in
  `Updates_required/`. The discipline the register imposes is on whoever writes
  the row: state the condition under which you would agree it is finished.

A BROKEN CHECK IS NOT A PASS

  The failure mode that would make this tool worse than useless is a check that
  errors and reads as success — the same shape as a reference nothing matches
  being invisible to the thing that would report it, which has caught this
  project four times. So:

      command exits non-zero  -> ERROR, and the run fails
      command produces nothing -> ERROR, and the run fails
      output != expect        -> OPEN
      output == expect        -> DONE

  ERROR is louder than OPEN, deliberately. An open task is work; a broken check
  is a lie waiting to happen.

ON RUNNING COMMANDS FROM A CSV

  `tools/task_register.csv` is tracked, reviewed in diff like any other file, and
  its commands run with the repo root as the working directory. The refusal list
  below is a TRIPWIRE, not a sandbox: it catches a destructive command arriving
  by accident or by careless copy-paste, and it would not stop anyone determined.
  Checks must be read-only. If one needs to write, it is not a check.

Usage:
    python3 tools/task_lint.py             # full report
    python3 tools/task_lint.py --quiet     # gate: fails only on a broken check
    python3 tools/task_lint.py --open      # just the open ones
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-25.

import argparse
import csv
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REGISTER = REPO / "tools/task_register.csv"
TIMEOUT = 120

# Tripwire, not a sandbox — see the docstring. A check that trips this is a
# mistake in the register, and the register is the thing to fix.
#
# Discarding stderr is read-only, and the first run of this tool refused three
# perfectly good checks over `2>/dev/null`. The guard was wrong, not the checks.
# It is stripped before the test rather than carved out of the pattern, because
# a redirect exemption written into a regex of forbidden redirects is a thing
# nobody will read correctly six months from now.
_DEVNULL = re.compile(r"\d*>>?\s*/dev/null")

FORBIDDEN = re.compile(
    r"(?:^|[\s;|&(])(?:rm|mv|cp|dd|mkfs|chmod|chown|truncate|shred)\s"
    r"|>\s*[^&|]|>>|git\s+(?:push|commit|reset|checkout|clean|rm)\b",
    re.I)


def is_read_only(cmd: str) -> bool:
    return not FORBIDDEN.search(_DEVNULL.sub("", cmd))


def run_check(cmd: str) -> tuple[str | None, str]:
    """Returns (stdout-or-None, note). None means the check did not produce
    an answer, which is an ERROR and never a pass."""
    if not is_read_only(cmd):
        return None, "refused: the check is not read-only"
    try:
        p = subprocess.run(cmd, shell=True, cwd=REPO, timeout=TIMEOUT,
                           capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        return None, f"timed out after {TIMEOUT}s"
    if p.returncode != 0:
        err = (p.stderr or "").strip().split("\n")[-1][:90]
        return None, f"exit {p.returncode}: {err}"
    out = (p.stdout or "").strip()
    if out == "":
        return None, "produced no output — a check must answer"
    return out, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--open", action="store_true", dest="only_open")
    args = ap.parse_args()

    if not REGISTER.exists():
        print(f"  SKIP  {REGISTER.name} not in this checkout")
        return 0

    with REGISTER.open(encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("id", "").strip()]

    done, open_, errors = [], [], []
    for r in rows:
        out, note = run_check(r["check"])
        if out is None:
            errors.append((r, note))
        elif out == r["expect"].strip():
            done.append(r)
        else:
            open_.append((r, out))

    if errors:
        print(f"  FAIL  {len(errors)} check(s) could not answer — "
              f"a broken check is not a pass:")
        for r, note in errors:
            print(f"          {r['id']}  {r['title'][:52]}")
            print(f"                {note}")

    if not args.only_open and not args.quiet and done:
        print(f"\n  {len(done)} task(s) now satisfy their check "
              f"(remove the row, or leave it as a regression guard):")
        for r in done:
            print(f"      DONE  {r['id']}  {r['title'][:64]}")

    if open_ and not args.quiet:
        print(f"\n  {len(open_)} open:")
        for r, out in sorted(open_, key=lambda x: x[0]["id"]):
            impl = f"  [{r['implements']}]" if r.get("implements") else ""
            print(f"      OPEN  {r['id']}  {r['title'][:60]}{impl}")
            print(f"                {out}  (want {r['expect'].strip()})"
                  f"   opened {r.get('opened','')}")

    if args.quiet:
        print("task_lint: " + ("FAIL" if errors else "OK"))
    else:
        print(f"\n  {len(rows)} task(s): {len(done)} done, {len(open_)} open, "
              f"{len(errors)} broken")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
